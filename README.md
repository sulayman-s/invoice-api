# PDF Data Extraction API

This project is a FastAPI application that allows you to upload PDF files, extract metadata, and store the results in Elasticsearch. You can also check the status of the PDF processing through various endpoints.

## Directory Structure

project_root/
│
├── data_pdfs/
├── pdf_data_extractor.py
├── main.py
├── requirements.txt
└── start_elasticsearch_kibana.sh


## Files

### 1. `pdf_data_extractor.py`

The script to extract data from a PDF.


### 2. main.py

The FastAPI application to handle PDF uploads and interact with Elasticsearch.

### 3. requirements.txt

List of Python dependencies.


### 4. start_elasticsearch_kibana.sh

A shell script to start Elasticsearch and Kibana using Docker.

```
#!/bin/bash

# Start Elasticsearch
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" docker.elastic.co/elasticsearch/elasticsearch:7.17.0

# Start Kibana
docker run -d --name kibana -p 5601:5601 --link elasticsearch:elasticsearch docker.elastic.co/kibana/kibana:7.17.0

```

## Instructions
Set Up Elasticsearch and Kibana

Run the following script to start Elasticsearch and Kibana using Docker:

```
chmod +x start_elasticsearch_kibana.sh
./start_elasticsearch_kibana.sh
```

## Install Python Dependencies

Ensure you have Python installed, then install the dependencies using pip:

```
pip install -r requirements.txt
```

## Run the FastAPI Application

Start the FastAPI application using uvicorn:

```
uvicorn main:app --reload
```

## Interact with the API

You can now upload PDF files and check their statuses via the API endpoints. The uploaded PDFs will be saved in the data_pdfs directory. Use tools like curl or Postman to test the endpoints.
Example curl Commands

To test the upload-pdf endpoint:

```
curl -X POST "http://127.0.0.1:8000/upload-pdf/" -F "file=@path/to/your/file.pdf"

```

To check the status of all documents:

```
curl -X GET "http://127.0.0.1:8000/status/"

```

To check the status of a specific document by its ID:

```
curl -X GET "http://127.0.0.1:8000/status/{doc_id}"

```

To check the status of a document by its filename:

```
curl -X GET "http://127.0.0.1:8000/status-by-filename/?filename=your_file.pdf"

```

To get the data of a specific document by its ID:

```
curl -X GET "http://127.0.0.1:8000/data/{doc_id}"

```

To get the data of a document by its filename:

```
curl -X GET "http://127.0.0.1:8000/data-by-filename/?filename=your_file.pdf"

```

To get all documents in the pdf_data index:

```
curl -X GET "http://127.0.0.1:8000/all-docs/"

```

By following these steps, you'll have Elasticsearch, Kibana, and the FastAPI application running and ready to handle PDF uploads, store their statuses, and retrieve extracted data from Elasticsearch.











