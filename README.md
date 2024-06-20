# PDF Data Extraction API

This project is a FastAPI application that allows you to upload PDF files, extract metadata, and store the results in SQLite. You can also check the status of the PDF processing and retrieve the extracted data through various endpoints.

## Directory Structure


project_root/
│
├── data_pdfs/
├── pdf_data_extractor.py
├── main.py
├── requirements.txt


## Files

### 1. `pdf_data_extractor.py`

The script to extract data from a PDF.

### 2. `main.py`

The FastAPI application to handle PDF uploads and interact with SQLite.

### 3. `requirements.txt`

List of Python dependencies.

## Instructions

### Install Python Dependencies

Ensure you have Python installed, then install the dependencies using pip:

```sh
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

By following these steps, you'll have the FastAPI application running and ready to handle PDF uploads, store their statuses, and retrieve extracted data from SQLite.











