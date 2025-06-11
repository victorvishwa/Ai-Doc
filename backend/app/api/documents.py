from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import PyPDF2
import io
from datetime import datetime
from bson import ObjectId
from ..core.auth import get_current_user
from ..services.document_service import process_document, index_document
from ..models.document import DocumentCreate, DocumentResponse
from ..core.database import db
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Received file upload request for file: {file.filename}")
        
        # Check for existing document with same filename
        existing_doc = await db.documents.find_one({"filename": file.filename})
        if existing_doc:
            logger.info(f"Found existing document with same filename: {file.filename}")
            # Delete the old document
            await db.documents.delete_one({"_id": existing_doc["_id"]})
            logger.info(f"Deleted old document: {file.filename}")
        
        # Read file content
        content = await file.read()
        logger.info(f"Successfully read file content, size: {len(content)} bytes")
        
        # Process different file types
        if file.filename.endswith('.pdf'):
            logger.info("Processing PDF file")
            try:
                # Extract text from PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                        logger.info(f"Extracted {len(page_text)} characters from page {page_num + 1}")
                logger.info(f"Successfully extracted text from PDF, total length: {len(text)}")
                
                # Log a sample of the extracted text
                sample_text = text[:200] + "..." if len(text) > 200 else text
                logger.info(f"Sample of extracted text: {sample_text}")
                
            except Exception as e:
                logger.error(f"Error processing PDF: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")
        elif file.filename.endswith('.txt'):
            logger.info("Processing TXT file")
            try:
                text = content.decode('utf-8')
                logger.info(f"Successfully decoded TXT file, length: {len(text)}")
            except Exception as e:
                logger.error(f"Error processing TXT file: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Error processing TXT file: {str(e)}")
        else:
            logger.error(f"Unsupported file format: {file.filename}")
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload a PDF or TXT file.")

        # Process and index the document
        logger.info("Processing document content")
        processed_doc = await process_document(text, file.filename)
        logger.info(f"Processed document length: {len(processed_doc)}")
        
        logger.info("Indexing document")
        indexed_doc = await index_document(processed_doc)
        logger.info("Document indexed successfully")

        # Store in database
        document = DocumentCreate(
            filename=file.filename,
            content=text,
            processed_content=processed_doc,
            uploaded_by=str(current_user["_id"]),
            upload_date=datetime.utcnow()
        )

        logger.info("Saving document to database")
        # Save to MongoDB
        result = await db.documents.insert_one(document.dict())
        logger.info(f"Document saved successfully with ID: {result.inserted_id}")
        
        # Verify the document was saved correctly
        saved_doc = await db.documents.find_one({"_id": result.inserted_id})
        if saved_doc:
            logger.info(f"Verified document saved with content length: {len(saved_doc.get('content', ''))}")
        else:
            logger.error("Failed to verify saved document")
        
        return DocumentResponse(
            id=str(result.inserted_id),
            filename=file.filename,
            upload_date=document.upload_date
        )

    except HTTPException as he:
        logger.error(f"HTTP Exception during upload: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")

@router.get("/list", response_model=List[DocumentResponse])
async def list_documents(
    current_user: dict = Depends(get_current_user)
):
    try:
        # Get documents sorted by upload date (newest first)
        documents = await db.documents.find().sort("upload_date", -1).to_list(length=None)
        logger.info(f"Found {len(documents)} documents")
        for doc in documents:
            logger.info(f"Document: {doc['filename']}, Content length: {len(doc.get('content', ''))}")
        return [
            DocumentResponse(
                id=str(doc["_id"]),
                filename=doc["filename"],
                upload_date=doc["upload_date"]
            ) for doc in documents
        ]
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        result = await db.documents.delete_one({"_id": ObjectId(document_id)})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": "Document deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 