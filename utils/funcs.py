import streamlit as st
from utils.rag_manager import get_rag_manager


def pin_piece(piece, state_var):
    # add pieces related to the article
    state_var.append(piece)
    st.session_state.review_pieces.append(piece)
    add_to_context(piece)
    # st.toast(f"**pinned successfully!**", icon="📌")


def unpin_piece(article, state_var):
    # unpin the article
    state_var.remove(article)
    if article in st.session_state.review_pieces:
        remove_from_lit_review(article)
    st.toast(f"**unpinned successfully!**", icon="↩️")


def clean_and_close_search():
    st.session_state.article_search_results = []


def show_pin_buttons(piece, state_var):
    if piece not in state_var:
        st.button(
            label="📌 **pin**",
            key=f"pin_{piece['id']}",
            use_container_width=True,
            type='primary',
            on_click=pin_piece,
            args=(piece, state_var,)
        )

    else:
        st.button(
            label="↩️ **unpin**",
            key=f"unpin_{piece['id']}",
            use_container_width=True,
            type='secondary',
            on_click=unpin_piece,
            args=(piece, state_var,)
        )


def add_to_context(article):
    info, interface_context = prepare_article_for_viewing(article)

    # check if info is in the messages to interface content
    if interface_context not in st.session_state.messages_to_interface_context:
        st.session_state.messages_to_interface_context.append(interface_context)
        st.session_state.messages_to_api_context.append(info)


def set_command_none():
    st.session_state.command = None
    clean_and_close_search()


def set_command_search():
    st.session_state.command = "\\search"


def set_command_pdf():
    st.session_state.command = "\\pdf"
    clean_and_close_search()


def set_command_review():
    st.session_state.command = "\\review"
    clean_and_close_search()


def review_action_buttons(article, state_var):
    # create 2 columns for the buttons
    col1, col2 = st.columns(2)
    with col1:
        if article not in st.session_state.review_pieces:
            # include in lit review button
            st.button(
                label="✅ Include",
                type="primary",
                use_container_width=True,
                key=f"include_{article['id']}",
                on_click=add_to_lit_review,
                args=(article,)
            )
        else:
            # remove from lit review button
            st.button(
                label="❌ Exclude",
                type="secondary",
                use_container_width=True,
                key=f"remove_{article['id']}",
                on_click=remove_from_lit_review,
                args=(article,)
            )
    with col2:
        # show button for unpinning
        show_pin_buttons(article, state_var)


def prepare_article_for_viewing(article):
    # Extract abstract/text content - try multiple possible keys
    abstract_text = ""
    if 'text' in article and article['text']:
        abstract_text = article['text']
    elif 'abstract' in article and article['abstract']:
        abstract_text = article['abstract']
    elif 'summary' in article and article['summary']:
        abstract_text = article['summary']
    
    # Ensure we have substantial content for the LLM
    if not abstract_text or len(abstract_text.strip()) < 50:
        # If no substantial abstract, include title and any available metadata
        title = article.get('title', 'Unknown Title')
        journal = article.get('journal', '')
        year = article.get('year', '')
        abstract_text = f"Title: {title}. Journal: {journal}. Year: {year}. [Abstract not available]"
    
    # Prepare citation information
    if 'authors' in article and 'year' in article:
        citation_info = f"{article['authors']}, {article['year']}"
        # Full context for LLM includes title, citation, and abstract
        info = f"**Study: {article.get('title', 'Unknown Title')}**\n**Authors & Year:** {citation_info}\n**DOI:** {article.get('doi', 'N/A')}\n**Journal:** {article.get('journal', 'N/A')}\n**Abstract:** {abstract_text}"
        # Short context for UI display
        interface_context = f"**{citation_info}** ({article.get('doi', 'N/A')})"
    else:
        citation = ""
        if 'citation' in article and article['citation']:
            citation = article['citation'][0] if isinstance(article['citation'], list) else article['citation']
        
        # Full context for LLM
        info = f"**Study: {article.get('title', 'Unknown Title')}**\n**Citation:** {citation}\n**DOI:** {article.get('doi', 'N/A')}\n**Journal:** {article.get('journal', 'N/A')}\n**Abstract:** {abstract_text}"
        # Short context for UI display
        interface_context = f"**{citation}** ({article.get('doi', 'N/A')})"
    
    return info, interface_context


# add to notes
def add_to_lit_review(article):
    # add article to lit review studies
    st.session_state.review_pieces.append(article)
    # info is the full article, interface context is only the citation or authors and year
    info, interface_context = prepare_article_for_viewing(article)

    # check if info is in the messages to interface content
    if interface_context not in st.session_state.messages_to_interface_context:
        st.session_state.messages_to_interface_context.append(interface_context)
        st.session_state.messages_to_api_context.append(info)


# remove from notes
def remove_from_lit_review(article):
    # remove article from lit review studies
    st.session_state.review_pieces.remove(article)
    # info is the full article, interface context is only the citation or authors and year
    info, interface_context = prepare_article_for_viewing(article)

    # check if info is in the messages to interface content
    if interface_context in st.session_state.messages_to_interface_context:
        st.session_state.messages_to_interface_context.remove(interface_context)
        st.session_state.messages_to_api_context.remove(info)
    st.toast(f"**Removed from 📚 literature review!**", icon="❌")


def add_rag_document_to_context(document):
    """Add a RAG document to the context using only its abstract (first 500 words)"""
    # Add to RAG documents list
    if document not in st.session_state.rag_documents:
        st.session_state.rag_documents.append(document)
    
    # Create abstract context entry
    abstract_info = f"**Study: {document['title']}**\n**Authors & Year:** {document['authors']}, {document['year']}\n**DOI:** {document['doi']}\n**Journal:** {document['journal']}\n**Abstract (First 500 words):** {document['abstract']}"
    abstract_context = f"**{document['short_citation']}** ({document['doi']})"
    
    # Add abstract to context if not already there
    if abstract_context not in st.session_state.messages_to_interface_context:
        st.session_state.messages_to_interface_context.append(abstract_context)
        st.session_state.messages_to_api_context.append(abstract_info)
        st.session_state.rag_abstracts.append(abstract_info)


def remove_rag_document_from_context(document):
    """Remove a RAG document from the context"""
    # Remove from RAG documents list
    if document in st.session_state.rag_documents:
        st.session_state.rag_documents.remove(document)
    
    # Remove abstract from context
    abstract_context = f"**{document['short_citation']}** ({document['doi']})"
    abstract_info = f"**Study: {document['title']}**\n**Authors & Year:** {document['authors']}, {document['year']}\n**DOI:** {document['doi']}\n**Journal:** {document['journal']}\n**Abstract (First 500 words):** {document['abstract']}"
    
    if abstract_context in st.session_state.messages_to_interface_context:
        st.session_state.messages_to_interface_context.remove(abstract_context)
    
    if abstract_info in st.session_state.messages_to_api_context:
        st.session_state.messages_to_api_context.remove(abstract_info)
    
    if abstract_info in st.session_state.rag_abstracts:
        st.session_state.rag_abstracts.remove(abstract_info)


def add_rag_query_results_to_context(query_results, query):
    """Add RAG query results to the context"""
    # Clear previous query results from context
    clear_rag_query_results_from_context()
    
    # Add new query results
    for i, result in enumerate(query_results[:5]):  # Top 5 results
        result_info = f"**RAG Result {i+1} for Query: '{query}'**\n**Source:** {result['metadata']['title']} ({result['metadata']['citation']})\n**Page:** {result['metadata']['page_number']}\n**Content:** {result['content']}"
        result_context = f"RAG Result {i+1}: {result['metadata']['title'][:30]}..."
        
        st.session_state.messages_to_interface_context.append(result_context)
        st.session_state.messages_to_api_context.append(result_info)
        st.session_state.rag_query_results.append(result_info)


def clear_rag_query_results_from_context():
    """Clear RAG query results from context"""
    # Remove all RAG query results from context
    for result_info in st.session_state.rag_query_results:
        if result_info in st.session_state.messages_to_api_context:
            st.session_state.messages_to_api_context.remove(result_info)
    
    # Remove RAG result contexts from interface context
    interface_contexts_to_remove = [ctx for ctx in st.session_state.messages_to_interface_context if ctx.startswith("RAG Result")]
    for ctx in interface_contexts_to_remove:
        st.session_state.messages_to_interface_context.remove(ctx)
    
    # Clear the RAG query results list
    st.session_state.rag_query_results = []


def get_rag_context_summary():
    """Get a summary of current RAG context"""
    num_documents = len(st.session_state.rag_documents)
    num_abstracts = len(st.session_state.rag_abstracts)
    num_query_results = len(st.session_state.rag_query_results)
    
    return {
        'documents': num_documents,
        'abstracts': num_abstracts,
        'query_results': num_query_results,
        'total_context_items': num_abstracts + num_query_results
    }
