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
import uuid
import hashlib
import sqlite3

app = FastAPI()

# Connect to SQLite database
conn = sqlite3.connect("pdf_data.db", check_same_thread=False)
cursor = conn.cursor()

# Create the pdf_data table if it doesn't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS pdf_data (
    id TEXT PRIMARY KEY,
    status TEXT,
    file_hash TEXT,
    data TEXT
)
''')
conn.commit()

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

def store_initial_status(file_hash):
    """Store the initial status along with the file hash in SQLite."""
    data = {"status": "processing", "file_hash": file_hash}
    cursor.execute("INSERT INTO pdf_data (id, status, file_hash, data) VALUES (?, ?, ?, ?)",
                   (file_hash, data["status"], data["file_hash"], json.dumps({})))
    conn.commit()
    return file_hash

def update_status(doc_id: str, filename_data: dict):
    filename_data["status"] = "complete"
    cursor.execute("UPDATE pdf_data SET status = ?, data = ? WHERE id = ?",
                   (filename_data["status"], json.dumps(filename_data), doc_id))
    conn.commit()

def process_file(file_path: str, doc_id: str):
    """Process the file and store its initial status in SQLite."""
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
    """Check if the given file hash already exists in SQLite."""
    cursor.execute("SELECT COUNT(*) FROM pdf_data WHERE file_hash = ?", (file_hash,))
    num_hash = cursor.fetchone()[0]
    return num_hash > 0

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
    
        doc_id = store_initial_status(file_hash)
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
        cursor.execute("SELECT id, status FROM pdf_data")
        statuses = [{"id": row[0], "status": row[1]} for row in cursor.fetchall()]
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{doc_id}")
async def get_status_by_id(doc_id: str):
    try:
        cursor.execute("SELECT id, status FROM pdf_data WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            return {"id": row[0], "status": row[1]}
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status-by-filename/")
async def get_status_by_filename(filename: str = Query(..., description="The filename to search for")):
    try:
        cursor.execute("SELECT id, status, data FROM pdf_data")
        statuses = []
        for row in cursor.fetchall():
            data = json.loads(row[2])
            if data.get("filename") == filename:
                statuses.append({"id": row[0], "status": row[1]})
        return {"statuses": statuses}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data/{doc_id}")
async def get_data_by_id(doc_id: str):
    try:
        cursor.execute("SELECT data FROM pdf_data WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        if row:
            return JSONResponse(content=json.loads(row[0]))
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/data-by-filename/")
async def get_data_by_filename(filename: str = Query(..., description="The filename to search for")):
    try:
        cursor.execute("SELECT data FROM pdf_data")
        data = []
        for row in cursor.fetchall():
            file_data = json.loads(row[0])
            if file_data.get("filename") == filename:
                data.append(file_data)
        if not data:
            raise HTTPException(status_code=404, detail="Data not found")
        return JSONResponse(content={"data": data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/all-docs/")
async def get_all_docs():
    try:
        cursor.execute("SELECT id, data FROM pdf_data")
        docs = [{"id": row[0], **json.loads(row[1])} for row in cursor.fetchall()]
        return JSONResponse(content={"documents": docs})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ensure the temp directory exists
if not os.path.exists("temp"):
    os.makedirs("temp")

