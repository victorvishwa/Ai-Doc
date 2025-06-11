from typing import List, Dict
import openai
from ..core.config import settings
from .document_service import search_documents
from ..core.database import db
import logging
from datetime import datetime
import re
from collections import Counter
from difflib import get_close_matches
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI and Groq clients
try:
    openai.api_key = settings.OPENAI_API_KEY
    if not openai.api_key:
        logger.error("OpenAI API key is not set")
except Exception as e:
    logger.error(f"Error initializing OpenAI client: {str(e)}")

try:
    groq_client = Groq(api_key=settings.GROQ_API_KEY)
    if not settings.GROQ_API_KEY:
        logger.error("Groq API key is not set")
except Exception as e:
    logger.error(f"Error initializing Groq client: {str(e)}")
    groq_client = None

def get_similar_terms(term: str, all_terms: List[str], cutoff: float = 0.6) -> List[str]:
    """
    Get similar terms using fuzzy matching
    """
    matches = get_close_matches(term, all_terms, n=3, cutoff=cutoff)
    return matches

def extract_terms_from_text(text: str) -> List[str]:
    """
    Extract meaningful terms from text
    """
    # Remove special characters and split into words
    words = re.findall(r'\b\w+\b', text.lower())
    # Filter out common words and short terms
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    terms = [word for word in words if word not in stop_words and len(word) > 2]
    return list(set(terms))

def clean_text(text: str) -> str:
    """
    Clean and normalize text
    """
    # Remove special characters and extra whitespace
    text = re.sub(r'[^\w\s.,!?-]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def calculate_relevance_score(sentence: str, query_terms: List[str]) -> float:
    """
    Calculate a relevance score for a sentence based on query terms
    """
    # Convert to lowercase for case-insensitive matching
    sentence_lower = sentence.lower()
    query_terms_lower = [term.lower() for term in query_terms]
    
    # Count exact matches
    exact_matches = sum(1 for term in query_terms_lower if term in sentence_lower)
    
    # Count word matches
    sentence_words = set(sentence_lower.split())
    word_matches = sum(1 for term in query_terms_lower if term in sentence_words)
    
    # Calculate base score
    base_score = exact_matches * 2 + word_matches
    
    # Bonus for sentences that contain multiple query terms
    if exact_matches > 1:
        base_score *= 1.5
    
    # Penalty for very long sentences
    if len(sentence.split()) > 30:
        base_score *= 0.8
    
    return base_score

def extract_relevant_sentences(text: str, query_terms: List[str], max_sentences: int = 3) -> str:
    """
    Extract the most relevant sentences from the text based on query terms
    """
    # Clean the text
    text = clean_text(text)
    logger.info(f"Cleaned text length: {len(text)}")
    
    # Split text into sentences
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    logger.info(f"Found {len(sentences)} sentences")
    
    # Score sentences based on relevance
    scored_sentences = []
    for sentence in sentences:
        score = calculate_relevance_score(sentence, query_terms)
        if score > 0:
            scored_sentences.append((score, sentence))
            logger.info(f"Sentence score: {score} - {sentence[:100]}...")
    
    # Sort by score and get top sentences
    scored_sentences.sort(reverse=True)
    relevant_sentences = [s[1] for s in scored_sentences[:max_sentences]]
    
    # If no relevant sentences found, return empty string
    if not relevant_sentences:
        logger.info("No relevant sentences found")
        return ""
    
    result = " ".join(relevant_sentences)
    logger.info(f"Extracted relevant text length: {len(result)}")
    return result

def format_structured_response(content: str) -> str:
    """
    Format the response into a structured format with clear sections
    """
    # Split content into sections
    sections = content.split('\n\n')
    formatted_response = []
    current_section = []
    
    for section in sections:
        section = section.strip()
        if not section:
            continue
            
        # Check if section is a list item or new section
        if section.startswith(('-', '*', '1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.')):
            if current_section:
                formatted_response.append('\n'.join(current_section))
                current_section = []
            formatted_response.append(section)
        elif section.startswith(('Definition:', 'Key Characteristics:', 'Impact:', 'Example:', 'Solution Approaches:', 'Challenges:')):
            if current_section:
                formatted_response.append('\n'.join(current_section))
                current_section = []
            formatted_response.append(f"\n{section}")
        else:
            current_section.append(section)
    
    if current_section:
        formatted_response.append('\n'.join(current_section))
    
    return '\n\n'.join(formatted_response)

def extract_relevant_content(text: str, query_terms: List[str]) -> str:
    """
    Extract relevant content based on query terms
    """
    # Split into paragraphs
    paragraphs = text.split('\n\n')
    relevant_paragraphs = []
    
    for paragraph in paragraphs:
        paragraph = clean_text(paragraph)
        if not paragraph:
            continue
            
        # Check if paragraph contains any query terms
        if any(term.lower() in paragraph.lower() for term in query_terms):
            # Get the sentences containing the terms
            sentences = re.split(r'[.!?]+', paragraph)
            relevant_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if any(term.lower() in sentence.lower() for term in query_terms):
                    relevant_sentences.append(sentence)
            
            if relevant_sentences:
                relevant_paragraphs.append(' '.join(relevant_sentences))
    
    return '\n\n'.join(relevant_paragraphs)

def generate_fallback_response(query: str, context: str) -> str:
    """
    Generate a fallback response when LLM is not available
    """
    try:
        # Extract query terms
        query_terms = [term.strip() for term in query.lower().split() if len(term.strip()) > 2]
        
        # Extract relevant content
        relevant_content = extract_relevant_content(context, query_terms)
        
        if relevant_content:
            # Format the response with sections
            response = f"Based on the documents, here's what I found about {query}:\n\n"
            response += "Definition:\n"
            response += "- " + relevant_content.split('.')[0] + ".\n\n"
            
            response += "Key Characteristics:\n"
            points = [p.strip() for p in relevant_content.split('.') if len(p.strip()) > 20]
            for point in points[:3]:
                response += f"- {point}.\n"
            
            response += "\nImpact:\n"
            response += "- " + points[3] if len(points) > 3 else "- Significant impact on the field.\n"
            
            return format_structured_response(response)
        else:
            return "I couldn't find specific information about your query in the documents."
            
    except Exception as e:
        logger.error(f"Error generating fallback response: {str(e)}")
        return "I found some documents but couldn't process them properly."

async def get_llm_response(query: str, context: str) -> str:
    """
    Get response from LLM using the provided context
    """
    try:
        if not groq_client or not settings.GROQ_API_KEY:
            logger.warning("Groq API key not set, using fallback response")
            return generate_fallback_response(query, context)
            
        prompt = f"""Based on the following context, please provide a clear and structured answer to the question.
        Format your response with the following sections:
        
        1. Definition: A clear definition of the concept
        2. Key Characteristics: List the main features or aspects
        3. Impact: Describe the effects or implications
        4. Example: Provide a concrete example if applicable
        5. Solution Approaches: List possible solutions or countermeasures
        6. Challenges: List the main challenges or limitations
        
        Use bullet points (-) for lists within each section.
        Focus only on information directly related to the question.
        If the answer cannot be found in the context, say so.
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:"""
        
        # Use Groq LLM for response
        completion = groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that provides clear and structured answers based on the provided context. Format responses with clear sections and bullet points."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_completion_tokens=1024,
            top_p=1,
            stream=False,
            stop=None
        )
        
        response = completion.choices[0].message.content
        return format_structured_response(response.strip())
        
    except Exception as e:
        logger.error(f"Error getting LLM response: {str(e)}")
        return generate_fallback_response(query, context)

async def process_query(query: str, user_id: str) -> Dict:
    """
    Process the user's query and return a focused response
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Get all documents, sorted by upload date (newest first)
        documents = await db.documents.find().sort("upload_date", -1).to_list(length=None)
        logger.info(f"Found {len(documents)} documents")
        
        if not documents:
            return {
                "answer": "I don't have any documents to search through yet. Please upload some documents first.",
                "sources": []
            }

        # Extract and clean query terms
        query_terms = [term.strip() for term in query.lower().split() if len(term.strip()) > 2]
        logger.info(f"Query terms: {query_terms}")
        
        # Search through document content
        relevant_docs = []
        for doc in documents:
            content = doc.get('content', '')
            if not content:
                continue
                
            # Log document info
            logger.info(f"Checking document: {doc['filename']}")
            
            # Check if any terms are in the content
            if any(term in content.lower() for term in query_terms):
                logger.info(f"Found relevant content in {doc['filename']}")
                relevant_docs.append(doc)

        if not relevant_docs:
            logger.info("No relevant documents found")
            return {
                "answer": "I couldn't find any relevant information in the documents for your query.",
                "sources": []
            }

        # Prepare context from relevant documents
        context_parts = []
        sources = []
        
        for doc in relevant_docs:
            content = doc.get('content', '')
            if content:
                # Extract relevant content
                relevant_content = extract_relevant_content(content, query_terms)
                if relevant_content:
                    context_parts.append(f"From {doc['filename']}:\n{relevant_content}")
                    sources.append(doc['filename'])
        
        # Combine context
        context = "\n\n".join(context_parts)
        logger.info(f"Combined context length: {len(context)}")
        
        # Get response
        answer = await get_llm_response(query, context)
        
        return {
            "answer": answer,
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return {
            "answer": "I encountered an error while processing your query. Please try again.",
            "sources": []
        }

async def get_chat_history(user_id: str, limit: int = 50) -> List[Dict]:
    """
    Get chat history for a user
    """
    try:
        history = await db.chat_history.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(limit).to_list(length=None)
        return history
    except Exception as e:
        logger.error(f"Error getting chat history: {str(e)}")
        return []

async def process_query_with_context(query: str, user_id: str) -> Dict:
    """
    Process a user query and generate a response using OpenAI GPT
    """
    try:
        # Search for relevant document chunks
        relevant_chunks = await search_documents(query)
        
        if not relevant_chunks:
            return {
                "answer": "I couldn't find any relevant information in the documentation to answer your question.",
                "sources": []
            }
        
        # Prepare context from relevant chunks
        context = "\n".join([chunk["text"] for chunk in relevant_chunks])
        
        # Generate response using OpenAI
        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on the provided documentation. If you cannot find the answer in the documentation, say so."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        
        # Extract sources from relevant chunks
        sources = [f"Document chunk {i+1}" for i in range(len(relevant_chunks))]
        
        return {
            "answer": response.choices[0].message.content,
            "sources": sources
        }
    except Exception as e:
        return {
            "answer": "I apologize, but I encountered an error while processing your query. Please try again later.",
            "sources": []
        } 