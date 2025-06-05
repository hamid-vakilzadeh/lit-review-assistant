import streamlit as st
from utils.ai import ai_completion
from utils.funcs import (
    pin_piece,
    add_rag_document_to_context, remove_rag_document_from_context,
    add_rag_query_results_to_context,
    get_rag_context_summary
)
from utils.session_state_vars import ensure_session_state_vars
import json
import time
from tabs import article_search
from utils.local_storage import (
    delete_chat,
    get_chat,
    get_all_chats,
    update_chat,
    add_new_message,
    clear_chat_messages
)

ensure_session_state_vars()

@st.dialog("🔍 Advanced Article Search", width="large")
def advanced_search_dialog():
    article_search.advanced_search()
    if st.button("Close", type="secondary"):
        st.session_state.show_advanced_search = False
        st.rerun()

@st.dialog("🔎 Quick Article Search", width="large") 
def quick_search_dialog():
    article_search.article_search()
    if st.button("Close", type="secondary"):
        st.session_state.show_quick_search = False
        st.rerun()

def improved_interface():
    """
    Improved user interface for AIRA with better UX and clearer workflow
    """
    
    # Initialize chat management
    if 'all_messages' not in st.session_state:
        st.session_state.all_messages = get_all_chats()

    if len(st.session_state.all_messages) == 0:
        st.session_state.all_messages = get_all_chats()

    # Automatically use the first (and only) chat - no selection needed
    if 'chat_id' not in st.session_state:
        st.session_state.chat_id = list(st.session_state.all_messages.keys())[0]
    
    # Initialize current_chat_name early to prevent AttributeError
    if 'current_chat_name' not in st.session_state:
        if st.session_state.get('chat_id') and st.session_state.chat_id in st.session_state.all_messages:
            st.session_state.current_chat_name = st.session_state.all_messages[st.session_state.chat_id]['chat_name']
        else:
            st.session_state.current_chat_name = "New Chat"

    # Header with clear branding and navigation
    st.markdown("# 🤖 AIRA: AI Research Assistant")
    st.markdown("*Synthesize research papers with AI assistance*")
    
    # Main layout with three columns
    left_col, main_col, right_col = st.columns([1, 2, 1])
    
    with left_col:
        render_chat_management()
        render_research_tools()
    
    with main_col:
        render_main_chat_interface()
    
    with right_col:
        render_context_panel()
    
    # Show search dialogs based on session state
    if st.session_state.get('show_advanced_search', False):
        advanced_search_dialog()
    elif st.session_state.get('show_quick_search', False):
        quick_search_dialog()

def render_chat_management():
    """Render simplified chat controls - only clear functionality"""
    st.markdown("### 💬 Chat")
    
    # Only keep the clear button
    if st.button("🗑️ Clear Chat", use_container_width=True, type="secondary"):
        clear_chat_only()

def render_research_tools():
    """Render research tools section"""
    st.markdown("### 🔍 Research Tools")
    
    # Search Articles

    if st.button("🔍 Advanced Search", use_container_width=True, type="primary"):
        st.session_state.show_advanced_search = True
        st.session_state.show_quick_search = False
        
    
    # Upload PDFs - Multiple files support
    uploaded_files = st.file_uploader(
        "Upload PDFs",
        type=["pdf"],
        key='rag_pdf_upload',
        accept_multiple_files=True,
        help="Upload multiple PDF files to add to your research collection"
    )
            
    if st.button("📤 Upload & Process", use_container_width=True, type="primary"):
        if uploaded_files:
            process_multiple_pdfs(uploaded_files, doi_input=None)
    
    # Model Selection
    st.markdown("### ⚙️ Settings")
    chosen_model = st.selectbox(
        'AI Model',
        options=[
            'OpenAI: GPT-4o',
            'Anthropic: Claude 3.5 Sonnet',
            'Google: Gemini Flash 1.5',
        ],
    )
    
    # Update model selection
    model_mapping = {
        'OpenAI: GPT-4o': 'openai/gpt-4o',
        'Anthropic: Claude 3.5 Sonnet': 'anthropic/claude-3.5-sonnet',
        'Google: Gemini Flash 1.5': 'google/gemini-flash-1.5'
    }
    st.session_state.selected_model = model_mapping[chosen_model]

def render_main_chat_interface():
    """Render the main chat interface"""
    st.markdown("### 💭 Research Chat")
    
    # Ensure session state is properly initialized
    if 'review_pieces' not in st.session_state:
        ensure_session_state_vars()
    
    # Context status indicator
    context_count = len(st.session_state.review_pieces)
    if context_count == 0:
        st.warning("⚠️ No research papers in context. Add papers using the research tools.")
    else:
        st.success(f"✅ {context_count} research papers in context")
    
    # Initialize chat messages
    if "messages_to_interface" not in st.session_state:
        load_chat_messages()
    
    # Chat display
    chat_container = st.container(height=500)
    with chat_container:
        for message in st.session_state.messages_to_interface:
            with st.chat_message(message["role"]):
                if message["role"] == "user" and "context" in message:
                    # Show context in an expander for user messages
                    with st.expander("📚 Research Context Used"):
                        for item in message["context"]:
                            st.markdown(f"• {item}...")
                st.markdown(message["content"])
    
    # Chat input
    user_input = st.chat_input("Ask about your research papers...")
    
    if user_input:
        handle_user_input(user_input, chat_container)

def render_context_panel():
    """Render the research context panel with RAG information"""
    st.markdown("### 📚 Research Context")
    
    # Ensure session state is properly initialized
    if 'pinned_articles' not in st.session_state or 'pinned_pdfs' not in st.session_state or 'review_pieces' not in st.session_state:
        ensure_session_state_vars()
    
    # RAG Context summary
    rag_summary = get_rag_context_summary()
    total_articles = len(st.session_state.pinned_articles)
    total_rag_docs = rag_summary['documents']
    context_items = len(st.session_state.review_pieces)
    
    st.metric("Articles Found", total_articles)
    st.metric("RAG Documents", total_rag_docs)
    st.metric("In Context", context_items)
    
    # RAG Management Section
    if total_rag_docs > 0:
        st.markdown("#### 🔍 RAG System")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Abstracts", rag_summary['abstracts'])
        with col2:
            st.metric("Query Results", rag_summary['query_results'])
        
        # Show RAG documents
        if st.session_state.rag_documents:
            with st.expander("📄 RAG Documents"):
                for i, doc in enumerate(st.session_state.rag_documents):
                    st.markdown(f"**{i+1}.** {doc['title'][:50]}...")
                    st.markdown(f"   *{doc['authors']} ({doc['year']})*")
                    if st.button("Remove from RAG", key=f"remove_rag_{i}", type="secondary"):
                        remove_rag_document_from_context(doc)
                        st.rerun()
    
    # Context management
    if context_items > 0:
        if st.button("🗑️ Clear All Context", type="secondary", use_container_width=True):
            clear_all_context()
    
    # Show context items
    if st.session_state.review_pieces:
        st.markdown("#### Current Context:")
        for i, item in enumerate(st.session_state.review_pieces[:5]):  # Show first 5
            with st.expander(f"📄 {item.get('title', 'Research Item')[:30]}..."):
                st.markdown(f"**Authors:** {item.get('authors', 'N/A')}")
                st.markdown(f"**Year:** {item.get('year', 'N/A')}")
                st.markdown(f"**DOI:** {item.get('doi', 'N/A')}")
                if st.button("Remove", key=f"remove_{i}", type="secondary"):
                    remove_from_context(i)
        
        if len(st.session_state.review_pieces) > 5:
            st.markdown(f"... and {len(st.session_state.review_pieces) - 5} more items")

def process_multiple_pdfs(uploaded_files, doi_input):
    """Process multiple PDF uploads using RAG system"""
    try:
        from utils.rag_manager import get_rag_manager
        rag_manager = get_rag_manager()
        
        success_count = 0
        total_files = len(uploaded_files)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, uploaded_file in enumerate(uploaded_files):
            try:
                status_text.text(f"Processing {uploaded_file.name}...")
                progress_bar.progress((i + 1) / total_files)
                
                # Reset file pointer to beginning
                uploaded_file.seek(0)
                
                # Add PDF to RAG system
                result = rag_manager.add_pdf_to_rag(uploaded_file, doi_input if i == 0 else None)
                
                if result['success']:
                    # Add document to context (abstract only)
                    add_rag_document_to_context(result['document'])
                    success_count += 1
                    st.success(f"✅ {uploaded_file.name}: Successfully processed")
                else:
                    st.error(f"❌ {uploaded_file.name}: {result['message']}")
                    
            except Exception as file_error:
                st.error(f"❌ {uploaded_file.name}: Error processing file - {str(file_error)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        if success_count > 0:
            st.success(f"🎉 Successfully processed {success_count}/{total_files} PDFs!")
            st.rerun()
        else:
            st.error("❌ No PDFs were processed successfully.")
            
    except Exception as e:
        st.error(f"❌ Error initializing PDF processing: {str(e)}")
        st.info("💡 Try refreshing the page and uploading PDFs again.")

def process_pdf_upload(uploaded_file, doi_input):
    """Process single PDF upload - legacy function for compatibility"""
    process_multiple_pdfs([uploaded_file], doi_input)

def handle_user_input(user_input, chat_container):
    """Handle user input with RAG query functionality"""
    with chat_container:
        # Perform RAG query if we have documents
        if st.session_state.rag_documents:
            with st.spinner("Searching relevant content..."):
                from utils.rag_manager import get_rag_manager
                rag_manager = get_rag_manager()
                
                # Query RAG system for relevant content
                rag_results = rag_manager.query_rag(user_input, top_k=5)
                
                if rag_results['success'] and rag_results['results']:
                    # Add RAG results to context
                    add_rag_query_results_to_context(rag_results['results'], user_input)
        
        # Add user message with context
        context = st.session_state.messages_to_interface_context
        user_message = {
            "role": "user", 
            "content": user_input,
            "context": context
        }
        st.session_state.messages_to_interface.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            if context:
                with st.expander("📚 Research Context Used"):
                    for item in context:
                        st.markdown(f"• {item[:100]}...")
            st.markdown(user_input)
        
        # Generate AI response
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            with st.spinner("AI is thinking..."):
                response = generate_ai_response(user_input, context)
                
                # Stream response
                full_response = ""
                for chunk in response:
                    full_response += chunk
                    response_placeholder.markdown(full_response)
        
        # Add assistant message
        st.session_state.messages_to_interface.append({
            "role": "assistant", 
            "content": full_response
        })
        
        # Update chat storage
        update_chat(
            chat_id=st.session_state.chat_id,
            chat_name=st.session_state.current_chat_name,
            message_content=st.session_state.messages_to_interface,
            pinned_articles=st.session_state.pinned_articles,
            pinned_pdfs=st.session_state.pinned_pdfs,
        )

def generate_ai_response(user_input, context):
    """Generate AI response with improved prompting"""
    if len(st.session_state.review_pieces) == 0:
        # No context available
        yield "I need research papers to help you. Please use the **Research Tools** to:\n\n"
        yield "• 🔍 **Search Articles** - Find relevant research papers\n"
        yield "• 📁 **Upload PDFs** - Add your own research papers\n\n"
        yield "Once you add papers to your context, I can help you analyze and synthesize the research!"
        return
    
    # Prepare context
    context_text = '\n'.join(context) if context else 'No specific context provided'
    
    # Improved system prompt
    system_prompt = """You are AIRA, an AI Research Assistant specializing in literature review and research synthesis. 

Your role:
- Help researchers analyze and synthesize academic literature
- Identify themes, patterns, and gaps in research
- Provide insights based ONLY on the provided research papers
- Use proper APA citations for all claims
- Highlight areas of agreement and disagreement between studies

Guidelines:
- NEVER use knowledge outside the provided research papers
- Always cite sources using APA format (Author, Year)
- Be critical and analytical in your responses
- Identify methodological strengths and limitations
- Suggest areas for future research based on gaps you identify
"""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"""
Research Question/Request: {user_input}

Research Context:
{context_text}

Please provide a comprehensive response based on the research papers provided.
"""}
    ]
    
    try:
        response = ai_completion(
            messages=messages,
            model=st.session_state.selected_model,
            temperature=0.3,
            stream=True,
        )
        
        for line in response.iter_lines():
            if line and 'data' in line.decode('utf-8'):
                content = line.decode('utf-8').replace('data: ', '')
                if 'content' in content:
                    message = json.loads(content, strict=False)
                    if 'choices' in message and len(message['choices']) > 0:
                        delta = message['choices'][0].get('delta', {})
                        if 'content' in delta:
                            yield delta['content']
                            
    except Exception as e:
        yield f"❌ Error: The AI service is not responding. Please try again or select a different model: {str(e)}"

# Helper functions (keeping existing functionality)
def change_chat():
    st.session_state.pop('messages_to_interface', None)
    st.session_state.pop('all_messages', None)
    st.session_state.pop('messages_to_interface_context', None)
    st.session_state.pop('messages_to_api', None)
    st.session_state.pop('messages_to_api_context', None)
    st.session_state.pop('pinned_articles', None)
    st.session_state.pop('pinned_pdfs', None)
    st.session_state.pop('review_pieces', None)
    # Re-initialize session state after clearing
    ensure_session_state_vars()
    st.rerun()

def clear_chat():
    st.session_state.pop('chat_id', None)
    change_chat()

def clear_chat_only():
    """Clear only the messages in the current chat, keep the chat itself"""
    if st.session_state.get('chat_id'):
        clear_chat_messages(st.session_state.chat_id)
    # Clear only messages, not the entire chat
    st.session_state.pop('messages_to_interface', None)
    st.session_state.pop('messages_to_interface_context', None)
    st.session_state.pop('messages_to_api', None)
    st.session_state.pop('messages_to_api_context', None)
    # Re-initialize session state
    ensure_session_state_vars()
    st.rerun()

def delete_and_clear():
    """Delete the entire chat and clear session state"""
    if st.session_state.get('chat_id'):
        delete_chat(st.session_state.chat_id)
    change_chat()

def create_new_chat():
    """Create a new chat and switch to it"""
    chat_id = add_new_message(last_updated=time.time())
    st.session_state.chat_id = chat_id
    # Clear old session state and reinitialize
    st.session_state.pop('messages_to_interface', None)
    st.session_state.pop('messages_to_interface_context', None)
    st.session_state.pop('messages_to_api', None)
    st.session_state.pop('messages_to_api_context', None)
    st.session_state.pop('pinned_articles', None)
    st.session_state.pop('pinned_pdfs', None)
    st.session_state.pop('review_pieces', None)
    ensure_session_state_vars()
    # Refresh the chat list
    st.session_state.all_messages = get_all_chats()
    st.rerun()

def set_chat_name():
    st.session_state.change_name = True

def load_chat_messages():
    """Load chat messages for the current chat"""
    try:
        chat_content = get_chat(st.session_state.chat_id)
        if 'chat' in chat_content:
            st.session_state.messages_to_interface = chat_content['chat']
        else:
            st.session_state.messages_to_interface = []
            
        # Load pinned items
        if 'pdfs' in chat_content:
            for pdf in chat_content['pdfs']:
                pin_piece(pdf, st.session_state.pinned_pdfs)
        
        if 'articles' in chat_content:
            for article in chat_content['articles']:
                pin_piece(article, st.session_state.pinned_articles)
                
        st.session_state.messages_to_api = st.session_state.messages_to_interface.copy()
        
    except Exception as e:
        st.session_state.messages_to_interface = [{
            "role": "assistant",
            "content": f"👋 Hello! I'm AIRA, your AI Research Assistant. I can help you analyze and synthesize research papers.\n\n**To get started:**\n• Use the **Research Tools** to search for articles or upload PDFs\n• Add papers to your context\n• Ask me questions about your research! Error: {str(e)}"
        }]

def clear_all_context():
    """Clear all items from research context"""
    st.session_state.review_pieces = []
    st.session_state.messages_to_interface_context = []
    st.session_state.messages_to_api_context = []
    st.success("🗑️ Context cleared!")
    st.rerun()

def remove_from_context(index):
    """Remove specific item from context"""
    if 0 <= index < len(st.session_state.review_pieces):
        st.session_state.review_pieces.pop(index)
        # Also remove from context lists
        if index < len(st.session_state.messages_to_interface_context):
            st.session_state.messages_to_interface_context.pop(index)
        if index < len(st.session_state.messages_to_api_context):
            st.session_state.messages_to_api_context.pop(index)
        st.success("Removed from context!")
        st.rerun()
