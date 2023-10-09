import streamlit as st


def pin_piece(piece, state_var):
    # add pieces related to the article
    state_var.append(piece)
    st.toast(f"**pinned successfully!**", icon="📌")


def unpin_piece(article, state_var):
    # unpin the article
    state_var.remove(article)
    if article in st.session_state.review_pieces:
        st.session_state.review_pieces.remove(article)
    st.toast(f"**unpinned successfully!**", icon="↩️")


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


def add_to_context(articles):
    # add the article to the context
    selected_articles = []
    for article in articles:
        if 'authors' in article and 'year' in article:
            selected_articles.append(
                f"**From {article['authors']}, {article['year']}** ({article['doi']}): {article['text']}"
            )
        else:
            selected_articles.append(
                f"**From {article['citation']}** ({article['doi']}): {article['text']}"
            )

    selected_articles = "\n\n ".join(selected_articles)
    st.session_state.messages_to_interface.append({"role": "user", "content": selected_articles})
    st.session_state.messages_to_api.append({"role": "user", "content": selected_articles})
    st.session_state.pinned_articles = []
    st.session_state.article_search_results = []
    st.session_state.pinned_pdfs = []
    st.toast(f"**added successfully!**", icon="📌")