from typing import List, Dict, Any
import os
import openai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings
from ..core.database import db
import PyPDF2
import io
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize OpenAI client
try:
    openai.api_key = settings.OPENAI_API_KEY
    if not openai.api_key:
        logger.error("OpenAI API key is not set")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")

async def process_document(file_content: str, filename: str, user_id: str) -> Dict:
    """
    Process a document and store it in the database
    """
    try:
        # Store document in database
        document = {
            "content": file_content,
            "filename": filename,
            "user_id": user_id,
            "upload_date": datetime.utcnow()
        }
        result = await db.documents.insert_one(document)
        
        return {
            "id": str(result.inserted_id),
            "filename": filename,
            "upload_date": document["upload_date"]
        }
    except Exception as e:
        logger.error(f"Error processing document: {str(e)}")
        raise

async def get_user_documents(user_id: str) -> List[Dict]:
    """
    Get all documents for a user
    """
    try:
        documents = await db.documents.find(
            {"user_id": user_id}
        ).sort("upload_date", -1).to_list(length=None)
        
        return [{
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "upload_date": doc["upload_date"]
        } for doc in documents]
    except Exception as e:
        logger.error(f"Error getting user documents: {str(e)}")
        raise

async def process_document(content: str, filename: str) -> str:
    """
    Process the document content and return processed text
    """
    try:
        logger.info(f"Processing document: {filename}")
        
        # For PDF files, ensure we're getting clean text
        if filename.lower().endswith('.pdf'):
            try:
                # Convert content to bytes if it's a string
                if isinstance(content, str):
                    content = content.encode('utf-8')
                
                # Create PDF reader
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                
                # Extract text from each page
                text = ""
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                
                logger.info(f"Successfully extracted text from PDF: {filename}")
                return text.strip()
                
            except Exception as e:
                logger.error(f"Error processing PDF {filename}: {str(e)}")
                return content
        
        # For text files, just return the content
        return content.strip()
        
    except Exception as e:
        logger.error(f"Error in process_document: {str(e)}")
        return content

async def index_document(content: str) -> Dict[str, Any]:
    """
    Index the document content for searching
    """
    try:
        logger.info("Indexing document content")
        
        # For now, just return the content as is
        # In a real implementation, this would create search indices
        return {
            "content": content,
            "indexed": True
        }
        
    except Exception as e:
        logger.error(f"Error in index_document: {str(e)}")
        return {
            "content": content,
            "indexed": False
        }

async def search_documents(query: str, limit: int = 5) -> List[Dict]:
    """
    Search for relevant document chunks based on the query
    """
    try:
        embeddings = OpenAIEmbeddings()
        vector_store = MongoDBAtlasVectorSearch(
            collection=db.document_vectors,
            embedding=embeddings,
            index_name="default"
        )
        
        # Search for similar chunks
        results = vector_store.similarity_search(query, k=limit)
        
        return [{"text": doc.page_content, "score": doc.metadata.get("score", 0)} for doc in results]
    except Exception as e:
        return [] 