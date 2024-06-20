#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Jun  6 11:23:28 2024

@author: ssalie
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import os
import subprocess
import json
from typing import List
from elasticsearch import Elasticsearch
import uuid
import hashlib

app = FastAPI()
# Explicitly connect to Elasticsearch with scheme
es = Elasticsearch([{"host": "localhost", "port": 9200, "scheme": "http"}])
#es = Elasticsearch(['http://elasticsearch:9200'])

# create the pdf data index in elasticsearch
es.indices.create(index='pdf_data', ignore=400)

def extract_data(file_path: str) -> dict:
    result = subprocess.run(
        ['python', 'pdf_data_extractor.py', file_path],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to extract pdf file data: {result.stderr}")
    
    filename_json = result.stdout.strip()
    return json.loads(filename_json)

def store_initial_status(file_path, file_hash):
    """Store the initial status along with the file hash in Elasticsearch."""
    data = {"status": "processing", "file_hash": file_hash}
    es.index(index="pdf_data", id=file_hash, body=data)
    return file_hash

def update_status(doc_id: str, filename_data: dict):
    filename_data["status"] = "complete"
    es.update(index="pdf_data", id=doc_id, body={"doc": filename_data})

def process_file(file_path: str, doc_id: str):
    """Process the file and store its initial status in Elasticsearch."""
    try:
        # Process the file as usual
        filename_data = extract_data(file_path)
        update_status(doc_id, filename_data)
    finally:
        os.remove(file_path)

def compute_file_hash(file_path: str) -> str:
    """Compute the hash of the file located at file_path."""
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(65536)  # Read in 64KB chunks
            if not data:
                break
            hasher.update(data)
    return hasher.hexdigest()

def file_hash_already_exists(file_hash: str) -> bool:
    """Check if the given file hash already exists in Elasticsearch."""
    response = es.search(index="pdf_data", body={"query": {"term": {"file_hash": file_hash}}})
    num_hash = response["hits"]["total"]["value"]    
    if num_hash > 0:
        return True
    else:
        return False

@app.post("/upload-pdf/")
async def upload_pdf(background_tasks: BackgroundTasks, file: UploadFile = File(...)):    
    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())
    # Compute the hash of the file
    file_hash = compute_file_hash(file_location)

    if file_hash_already_exists(file_hash):
        os.remove(file_location)
        return {"status": "file has already been processed"}   
    else:     
    
        doc_id = store_initial_status(file_location, file_hash)
        background_tasks.add_task(process_file, file_location, doc_id)
        return {"status": "processing", "id": doc_id}

@app.post("/upload-multiple-pdfs/")
async def upload_multiple_pdfs(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    doc_ids = []
    for file in files:
        file_location = f"temp/{file.filename}"
        with open(file_location, "wb") as f:
            f.write(file.file.read())
        
        doc_id = store_initial_status(file_location)
        background_tasks.add_task(process_file, file_location, doc_id)
        doc_ids.append(doc_id)
    
    return {"status": "processing", "ids": doc_ids}

@app.post("/process-directory/")
async def process_directory(background_tasks: BackgroundTasks, directory: str):
    if not os.path.isdir(directory):
        raise HTTPException(status_code=400, detail="Invalid directory path")
    
    doc_ids = []
    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            file_path = os.path.join(directory, filename)
            doc_id = store_initial_status(file_path)
            background_tasks.add_task(process_file, file_path, doc_id)
            doc_ids.append(doc_id)
    
    return {"status": "processing", "ids": doc_ids}

@app.get("/status/")
async def get_all_statuses():
    try:
        response = es.search(index="pdf_data", body={"query": {"match_all": {}}})
        statuses = [{"id": hit["_id"], "status": hit["_source"]["status"]} for hit in response["hits"]["hits"]]
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{doc_id}")
async def get_status_by_id(doc_id: str):
    try:
        response = es.get(index="pdf_data", id=doc_id)
        return {"id": response["_id"], "status": response["_source"]["status"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status-by-filename/")
async def get_status_by_filename(filename: str = Query(..., description="The filename to search for")):
    try:
        response = es.search(index="pdf_data", body={
            "query": {
                "match": {
                    "filename": filename
                }
            }
        })
        statuses = [{"id": hit["_id"], "status": hit["_source"]["status"]} for hit in response["hits"]["hits"]]
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{doc_id}")
async def get_data_by_id(doc_id: str):
    try:
        response = es.get(index="pdf_data", id=doc_id)
        return JSONResponse(content=response["_source"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-by-filename/")
async def get_data_by_filename(filename: str = Query(..., description="The filename to search for")):
    try:
        response = es.search(index="pdf_data", body={
            "query": {
                "match": {
                    "filename": filename
                }
            }
        })
        if response["hits"]["total"]["value"] == 0:
            raise HTTPException(status_code=404, detail="Data not found")
        data = [hit["_source"] for hit in response["hits"]["hits"]]
        return JSONResponse(content={"data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all-docs/")
async def get_all_docs():
    try:
        response = es.search(index="pdf_data", body={"query": {"match_all": {}}}, size=10000)  # Adjust size as needed
        docs = [{"id": hit["_id"], **hit["_source"]} for hit in response["hits"]["hits"]]
        return JSONResponse(content={"documents": docs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ensure the temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp")
