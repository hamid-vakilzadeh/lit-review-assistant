import streamlit as st

# SQLite module replacement for ChromaDB compatibility
__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import chromadb
import time
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from utils.documentSearch import openai_ef
from utils.ai import ai_completion
from utils.doi import get_citation
import json
import re
from ast import literal_eval

class RAGManager:
    """Manages RAG functionality for multiple PDFs using ChromaDB"""
    
    def __init__(self):
        self.text_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=1000,  # Smaller chunks for better retrieval
            chunk_overlap=200
        )
        self.collection = self._get_collection()
    
    @st.cache_resource
    def _get_collection(_self):
        """Initialize ChromaDB collection for PDF storage"""
        try:
            if 'rag_client' not in st.session_state:
                # Use persistent client with a specific path
                import tempfile
                import os
                
                # Create a persistent directory for ChromaDB
                chroma_dir = os.path.join(tempfile.gettempdir(), "aira_chromadb")
                os.makedirs(chroma_dir, exist_ok=True)
                
                st.session_state.rag_client = chromadb.PersistentClient(path=chroma_dir)
            
            collection = st.session_state.rag_client.get_or_create_collection(
                "research_papers",
                embedding_function=openai_ef
            )
            return collection
        except Exception as e:
            st.warning(f"ChromaDB initialization failed: {str(e)}. Using in-memory client.")
            # Fallback to in-memory client
            st.session_state.rag_client = chromadb.Client()
            collection = st.session_state.rag_client.get_or_create_collection(
                "research_papers",
                embedding_function=openai_ef
            )
            return collection
    
    def extract_pdf_text(self, uploaded_file) -> Dict[str, Any]:
        """Extract text from uploaded PDF file"""
        try:
            pdf_reader = PdfReader(uploaded_file)
            all_text = ""
            pdf_chunks = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                all_text += page_text + "\n"
                
                # Create chunks for this page
                docs = self.text_splitter.create_documents([page_text])
                for doc_idx, doc in enumerate(docs):
                    doc.metadata['page_number'] = page_num + 1
                    doc.metadata['chunk_id'] = f"page_{page_num + 1}_chunk_{doc_idx}"
                    pdf_chunks.append(doc)
            
            # Extract title from first page
            title = self._extract_title_from_text(all_text[:2000])
            
            # Get first 500 words as abstract
            words = all_text.split()
            abstract = " ".join(words[:500]) if len(words) >= 500 else all_text
            
            return {
                'title': title,
                'abstract': abstract,
                'full_text': all_text,
                'chunks': pdf_chunks,
                'num_pages': len(pdf_reader.pages),
                'word_count': len(words)
            }
            
        except Exception as e:
            raise Exception(f"Error extracting PDF text: {str(e)}")
    
    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from the beginning of the PDF text"""
        try:
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                # Look for a substantial line that could be a title
                if (10 < len(line) < 200 and 
                    not line.lower().startswith(('abstract', 'introduction', 'keywords', 'doi:', 'http'))):
                    # Remove common artifacts
                    line = re.sub(r'^[^\w]*', '', line)  # Remove leading non-word chars
                    line = re.sub(r'[^\w]*$', '', line)  # Remove trailing non-word chars
                    if len(line) > 10:
                        return line
            return "Uploaded Document"
        except:
            return "Uploaded Document"
    
    def _extract_citation_with_ai(self, text: str) -> Dict[str, str]:
        """Use AI to extract citation information from PDF text"""
        try:
            prompt = f"""
            Extract bibliographic information from this academic paper text and return it as a JSON object.
            
            Text from paper (first 3000 characters):
            {text[:3000]}
            
            Return ONLY a valid JSON object with these fields:
            {{
                "authors": "Last, F. M., & Last2, F. M.",
                "year": "2024",
                "title": "Paper Title",
                "journal": "Journal Name",
                "full_citation": "Last, F. M., & Last2, F. M. (2024). Paper Title. Journal Name, 15(2), 123-145.",
                "short_citation": "Last et al., 2024"
            }}
            
            If you cannot extract certain information, use "Unknown" for that field.
            Return only the JSON object, no other text.
            """
            
            response = ai_completion(
                messages=[{"role": "user", "content": prompt}],
                model='openai/gpt-4o',
                temperature=0,
                stream=False,
            )
            
            citation_text = response.json()['choices'][0]['message']['content']
            
            # Extract JSON from response
            start_idx = citation_text.find('{')
            end_idx = citation_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                citation_json = json.loads(citation_text[start_idx:end_idx])
                return citation_json
            else:
                return self._default_citation()
                
        except Exception as e:
            st.warning(f"Could not extract citation automatically: {str(e)}")
            return self._default_citation()
    
    def _default_citation(self) -> Dict[str, str]:
        """Return default citation structure"""
        current_year = str(time.localtime().tm_year)
        return {
            "authors": "Unknown Authors",
            "year": current_year,
            "title": "Uploaded Document",
            "journal": "Unknown Journal",
            "full_citation": f"Unknown Authors ({current_year}). Uploaded Document. Unknown Journal.",
            "short_citation": f"Unknown, {current_year}"
        }
    
    def add_pdf_to_rag(self, uploaded_file, doi_input: Optional[str] = None) -> Dict[str, Any]:
        """Add a PDF to the RAG system"""
        try:
            # Extract text and metadata
            pdf_data = self.extract_pdf_text(uploaded_file)
            
            # Get citation information
            if doi_input and doi_input.strip():
                try:
                    full_citation = get_citation(doi_input.strip())
                    # Parse the citation to extract components
                    citation_info = self._parse_citation(full_citation)
                    citation_info['doi'] = doi_input.strip()
                except:
                    st.warning("Could not retrieve citation from DOI, using AI extraction...")
                    citation_info = self._extract_citation_with_ai(pdf_data['full_text'])
                    citation_info['doi'] = doi_input.strip()
            else:
                citation_info = self._extract_citation_with_ai(pdf_data['full_text'])
                citation_info['doi'] = f"uploaded_{int(time.time())}"
            
            # Create document ID
            doc_id = f"pdf_{int(time.time())}"
            
            # Create document object
            document = {
                'id': doc_id,
                'title': citation_info.get('title', pdf_data['title']),
                'authors': citation_info.get('authors', 'Unknown Authors'),
                'year': citation_info.get('year', str(time.localtime().tm_year)),
                'journal': citation_info.get('journal', 'Unknown Journal'),
                'doi': citation_info.get('doi', doc_id),
                'citation': citation_info.get('full_citation', f"Unknown ({citation_info.get('year', '2024')}). {pdf_data['title']}."),
                'short_citation': citation_info.get('short_citation', f"Unknown, {citation_info.get('year', '2024')}"),
                'abstract': pdf_data['abstract'],  # First 500 words
                'full_text': pdf_data['full_text'],
                'num_pages': pdf_data['num_pages'],
                'word_count': pdf_data['word_count'],
                'type': 'pdf',
                'source': 'uploaded',
                'upload_time': time.time()
            }
            
            # Store chunks in ChromaDB
            self._store_chunks_in_chromadb(document, pdf_data['chunks'])
            
            return {
                'success': True,
                'document': document,
                'message': f"✅ Successfully added '{document['title'][:50]}...' to RAG system ({pdf_data['num_pages']} pages, {pdf_data['word_count']} words)"
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': f"❌ Error adding PDF to RAG: {str(e)}"
            }
    
    def _parse_citation(self, citation: str) -> Dict[str, str]:
        """Parse a full citation string into components"""
        try:
            # Extract year
            year_match = re.search(r'\((\d{4})\)', citation)
            year = year_match.group(1) if year_match else str(time.localtime().tm_year)
            
            # Extract authors (text before year)
            if year_match:
                authors = citation[:year_match.start()].strip().rstrip('.,')
            else:
                authors = "Unknown Authors"
            
            # Extract title (text between year and journal)
            title_match = re.search(r'\(\d{4}\)\.\s*([^.]+)', citation)
            title = title_match.group(1).strip() if title_match else "Unknown Title"
            
            # Extract journal (remaining text)
            journal_match = re.search(r'\.\s*([^.]+)\.\s*$', citation)
            journal = journal_match.group(1).strip() if journal_match else "Unknown Journal"
            
            # Create short citation
            first_author = authors.split(',')[0] if ',' in authors else authors
            short_citation = f"{first_author}, {year}"
            
            return {
                'authors': authors,
                'year': year,
                'title': title,
                'journal': journal,
                'full_citation': citation,
                'short_citation': short_citation
            }
        except:
            return self._default_citation()
    
    def _store_chunks_in_chromadb(self, document: Dict[str, Any], chunks: List[Any]):
        """Store PDF chunks in ChromaDB"""
        try:
            # Prepare data for ChromaDB
            documents = [chunk.page_content for chunk in chunks]
            metadatas = [
                {
                    'doc_id': document['id'],
                    'title': document['title'],
                    'authors': document['authors'],
                    'year': str(document['year']),
                    'journal': document['journal'],
                    'page_number': chunk.metadata['page_number'],
                    'chunk_id': chunk.metadata['chunk_id'],
                    'citation': document['citation']
                }
                for chunk in chunks
            ]
            
            # Generate unique IDs for each chunk
            ids = [f"{document['id']}_{chunk.metadata['chunk_id']}" for chunk in chunks]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
        except Exception as e:
            st.warning(f"Could not store PDF chunks in vector database: {str(e)}")
    
    def query_rag(self, query: str, top_k: int = 5, doc_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """Query the RAG system for relevant content"""
        try:
            # Prepare filters
            where_filter = None
            if doc_ids:
                where_filter = {"doc_id": {"$in": doc_ids}}
            
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                where=where_filter,
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
                    formatted_results.append({
                        'content': doc,
                        'metadata': metadata,
                        'relevance_score': results['distances'][0][i] if 'distances' in results else 0
                    })
            
            return {
                'success': True,
                'results': formatted_results,
                'query': query,
                'total_results': len(formatted_results)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'query': query,
                'total_results': 0
            }
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents in the RAG system"""
        try:
            # Get all unique document IDs
            all_results = self.collection.get()
            doc_ids = set()
            documents = []
            
            if all_results['metadatas']:
                for metadata in all_results['metadatas']:
                    doc_id = metadata.get('doc_id')
                    if doc_id and doc_id not in doc_ids:
                        doc_ids.add(doc_id)
                        documents.append({
                            'id': doc_id,
                            'title': metadata.get('title', 'Unknown'),
                            'authors': metadata.get('authors', 'Unknown'),
                            'year': metadata.get('year', 'Unknown'),
                            'journal': metadata.get('journal', 'Unknown'),
                            'citation': metadata.get('citation', 'Unknown')
                        })
            
            return documents
            
        except Exception as e:
            st.error(f"Error retrieving documents: {str(e)}")
            return []
    
    def remove_document(self, doc_id: str) -> bool:
        """Remove a document and all its chunks from the RAG system"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(where={"doc_id": doc_id})
            
            if results['ids']:
                # Delete all chunks for this document
                self.collection.delete(ids=results['ids'])
                return True
            return False
            
        except Exception as e:
            st.error(f"Error removing document: {str(e)}")
            return False
    
    def clear_all_documents(self) -> bool:
        """Clear all documents from the RAG system"""
        try:
            # Delete the collection and recreate it
            st.session_state.rag_client.delete_collection("research_papers")
            self.collection = st.session_state.rag_client.get_or_create_collection(
                "research_papers",
                embedding_function=openai_ef
            )
            return True
            
        except Exception as e:
            st.error(f"Error clearing documents: {str(e)}")
            return False

# Global instance
@st.cache_resource
def get_rag_manager():
    """Get the global RAG manager instance"""
    return RAGManager()
