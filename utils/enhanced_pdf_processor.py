import streamlit as st
import time
import chromadb
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from utils.ai import ai_completion
from utils.doi import get_citation
from utils.documentSearch import openai_ef
from utils.funcs import pin_piece, add_to_lit_review
from ast import literal_eval
import json

# Text splitter for PDF processing
text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=2000,
    chunk_overlap=100
)

@st.cache_resource
def get_pdf_collection():
    """Initialize ChromaDB collection for PDF storage"""
    if 'memory_client' not in st.session_state:
        st.session_state.memory_client = chromadb.Client()
    
    st.session_state.pdf_collection = st.session_state.memory_client.get_or_create_collection(
        "pdf_documents",
        embedding_function=openai_ef
    )
    return st.session_state.pdf_collection

def extract_pdf_text(uploaded_file):
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PdfReader(uploaded_file)
        pdf_texts = []
        
        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extract_text()
            docs = text_splitter.create_documents([page_text])
            
            for doc_idx, doc in enumerate(docs):
                doc.metadata['page_number'] = page_num + 1
                doc.metadata['part_number'] = doc_idx
                pdf_texts.append(doc)
        
        return {
            'texts': pdf_texts,
            'num_pages': len(pdf_reader.pages),
            'title': extract_title_from_text(pdf_texts[:2]) if pdf_texts else "Unknown Document"
        }
    except Exception as e:
        raise Exception(f"Error extracting PDF text: {str(e)}")

def extract_title_from_text(first_pages):
    """Extract title from the first pages of the PDF"""
    try:
        combined_text = " ".join([doc.page_content for doc in first_pages])
        # Simple heuristic: take the first substantial line that looks like a title
        lines = combined_text.split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 10 and len(line) < 200 and not line.lower().startswith(('abstract', 'introduction', 'keywords')):
                return line
        return "Uploaded Document"
    except:
        return "Uploaded Document"

def get_citation_from_pdf_ai(pdf_texts):
    """Use AI to extract citation information from PDF"""
    try:
        # Combine first two pages for citation extraction
        first_pages_text = " ".join([doc.page_content for doc in pdf_texts[:4]])
        
        prompt = f"""
        Extract bibliographic information from this academic paper text and format it as an APA citation.
        
        Text from paper:
        {first_pages_text[:3000]}
        
        Please return ONLY a Python list with two elements:
        1. Full APA bibliography citation
        2. Short in-text citation format (Author, Year)
        
        Example format: ["Smith, J. (2023). Title of paper. Journal Name, 15(2), 123-145.", "Smith, 2023"]
        
        Return only the list, no other text.
        """
        
        response = ai_completion(
            messages=[{"role": "user", "content": prompt}],
            model='openai/gpt-4o',
            temperature=0,
            stream=False,
        )
        
        citation_text = response.json()['choices'][0]['message']['content']
        # Extract the list from the response
        start_idx = citation_text.find('[')
        end_idx = citation_text.rfind(']') + 1
        
        if start_idx != -1 and end_idx != -1:
            citation_list = literal_eval(citation_text[start_idx:end_idx])
            return citation_list
        else:
            return ["Unknown Citation", "Unknown, Year"]
            
    except Exception as e:
        st.warning(f"Could not extract citation automatically: {str(e)}")
        return ["Unknown Citation", "Unknown, Year"]

def process_pdf_for_context(uploaded_file, doi_input=None):
    """
    Process uploaded PDF and add to research context
    Returns: dict with processing results
    """
    try:
        # Extract text from PDF
        pdf_data = extract_pdf_text(uploaded_file)
        
        # Get citation information
        if doi_input and doi_input.strip():
            try:
                citation = get_citation(doi_input.strip())
                doi = doi_input.strip()
                short_citation = f"{citation.split('(')[0].strip()}, {citation.split('(')[1].split(')')[0]}" if '(' in citation else "Unknown, Year"
            except:
                st.warning("Could not retrieve citation from DOI, using AI extraction...")
                citation_data = get_citation_from_pdf_ai(pdf_data['texts'])
                citation = citation_data[0]
                short_citation = citation_data[1]
                doi = doi_input.strip()
        else:
            # Use AI to extract citation
            citation_data = get_citation_from_pdf_ai(pdf_data['texts'])
            citation = citation_data[0]
            short_citation = citation_data[1]
            doi = f"uploaded_{int(time.time())}"
        
        # Create document object for context
        pdf_document = {
            'id': int(time.time()),
            'title': pdf_data['title'],
            'authors': extract_authors_from_citation(citation),
            'year': extract_year_from_citation(citation),
            'doi': doi,
            'citation': citation,
            'short_citation': short_citation,
            'text': ' '.join([doc.page_content for doc in pdf_data['texts'][:5]]),  # First 5 chunks as abstract/content
            'abstract': ' '.join([doc.page_content for doc in pdf_data['texts'][:5]]),  # Ensure abstract field is available
            'full_text': pdf_data['texts'],
            'num_pages': pdf_data['num_pages'],
            'type': 'pdf',
            'source': 'uploaded',
            'journal': 'Uploaded PDF'  # Add journal field for consistency
        }
        
        # Store in ChromaDB for RAG
        pdf_collection = get_pdf_collection()
        store_pdf_in_chromadb(pdf_document, pdf_data['texts'], pdf_collection)
        
        # Add to session state
        pin_piece(pdf_document, st.session_state.pinned_pdfs)
        add_to_lit_review(pdf_document)
        
        return {
            'success': True,
            'document': pdf_document,
            'message': f"✅ Successfully processed '{pdf_data['title'][:50]}...' ({pdf_data['num_pages']} pages)"
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f"❌ Error processing PDF: {str(e)}"
        }

def store_pdf_in_chromadb(pdf_document, pdf_texts, collection):
    """Store PDF chunks in ChromaDB for RAG search"""
    try:
        doc_id = str(pdf_document['id'])
        
        # Prepare documents and metadata
        documents = [chunk.page_content for chunk in pdf_texts]
        metadatas = [
            {
                'doc_id': doc_id,
                'title': pdf_document['title'],
                'page_number': chunk.metadata['page_number'],
                'part_number': chunk.metadata['part_number'],
                'citation': pdf_document['citation']
            }
            for chunk in pdf_texts
        ]
        
        # Generate unique IDs for each chunk
        ids = [f"{doc_id}_page_{chunk.metadata['page_number']}_part_{chunk.metadata['part_number']}" 
               for chunk in pdf_texts]
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
    except Exception as e:
        st.warning(f"Could not store PDF in vector database: {str(e)}")

def extract_authors_from_citation(citation):
    """Extract authors from citation string"""
    try:
        # Simple extraction - take text before the year
        if '(' in citation:
            author_part = citation.split('(')[0].strip()
            # Remove trailing period or comma
            author_part = author_part.rstrip('.,')
            return author_part
        return "Unknown Authors"
    except:
        return "Unknown Authors"

def extract_year_from_citation(citation):
    """Extract year from citation string"""
    try:
        if '(' in citation and ')' in citation:
            year_part = citation.split('(')[1].split(')')[0]
            # Extract 4-digit year
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', year_part)
            if year_match:
                return int(year_match.group())
        return 2024  # Default to current year
    except:
        return 2024

def search_pdf_content(query, doc_id=None, top_k=5):
    """Search PDF content using RAG"""
    try:
        collection = get_pdf_collection()
        
        # Prepare search filters
        where_filter = {}
        if doc_id:
            where_filter['doc_id'] = str(doc_id)
        
        # Perform search
        results = collection.query(
            query_texts=[query],
            where=where_filter if where_filter else None,
            n_results=top_k
        )
        
        return {
            'success': True,
            'results': results,
            'documents': results['documents'][0] if results['documents'] else [],
            'metadatas': results['metadatas'][0] if results['metadatas'] else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'documents': [],
            'metadatas': []
        }

def generate_pdf_summary(pdf_document, query=None):
    """Generate AI summary of PDF content"""
    try:
        if query:
            # Search for relevant content
            search_results = search_pdf_content(query, pdf_document['id'])
            content = '\n'.join(search_results['documents'][:3])
            prompt_type = "question-specific"
        else:
            # Use first few chunks for general summary
            content = pdf_document['text']
            prompt_type = "general"
        
        if prompt_type == "general":
            system_prompt = """You are a research assistant helping to summarize academic papers. 
            Provide a concise summary highlighting:
            - Main research question/objective
            - Key methodology
            - Primary findings
            - Implications/contributions
            
            Use the provided citation format and keep the summary under 200 words."""
            
            user_prompt = f"""
            Paper: {pdf_document['citation']}
            
            Content to summarize:
            {content}
            
            Provide a structured summary of this research paper.
            """
        else:
            system_prompt = """You are a research assistant answering specific questions about academic papers.
            Base your answer ONLY on the provided content. If the content doesn't contain enough information
            to answer the question, say so clearly."""
            
            user_prompt = f"""
            Paper: {pdf_document['citation']}
            Question: {query}
            
            Relevant content:
            {content}
            
            Answer the question based on the provided content.
            """
        
        response = ai_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            model=st.session_state.selected_model,
            temperature=0.3,
            stream=True,
        )
        
        # Stream the response
        for line in response.iter_lines():
            if line and 'data' in line.decode('utf-8'):
                content = line.decode('utf-8').replace('data: ', '')
                if 'content' in content:
                    try:
                        message = json.loads(content, strict=False)
                        if 'choices' in message and len(message['choices']) > 0:
                            delta = message['choices'][0].get('delta', {})
                            if 'content' in delta:
                                yield delta['content']
                    except:
                        continue
                        
    except Exception as e:
        yield f"❌ Error generating summary: {str(e)}"
