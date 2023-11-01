import streamlit as st


def pin_piece(piece, state_var):
    # add pieces related to the article
    state_var.append(piece)
    st.session_state.review_pieces.append(piece)
    st.toast(f"**pinned successfully!**", icon="📌")


def unpin_piece(article, state_var):
    # unpin the article
    state_var.remove(article)
    if article in st.session_state.review_pieces:
        remove_from_lit_review(article)
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

    # selected_articles = []
    for article in articles:
        if 'authors' in article and 'year' in article:
            info = f"**From {article['authors']}, {article['year']}** ({article['doi']}): {article['text']}"
        else:
            citation = ""
            if 'citation' in article and article['citation']:
                citation = article['citation'][0]
            info = f"**From {citation}** ({article['doi']}): {article['text']}"

        # check if info is in the messages to interface content
        if info not in [message['content'] for message in st.session_state.messages_to_interface]:
            st.session_state.messages_to_interface.append({"role": "user", "content": info})
            st.session_state.messages_to_api.append({"role": "user", "content": info})


        # selected_articles.append(info)

        #st.session_state.messages_to_interface.append({"role": "user", "content": info})
        #st.session_state.messages_to_api.append({"role": "user", "content": info})
    #selected_articles = "\n\n ".join(selected_articles)
    # st.session_state.messages_to_interface.append({"role": "user", "content": selected_articles})
    # st.session_state.messages_to_api.append({"role": "user", "content": selected_articles})
    # st.session_state.pinned_articles = []
    st.session_state.article_search_results = []
    # st.session_state.pinned_pdfs = []
    st.session_state.command = None
    st.toast(f"**added successfully!**", icon="📌")


def set_command_none():
    st.session_state.command = None


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


# add to notes
def add_to_lit_review(article):
    # add article to lit review studies
    st.session_state.review_pieces.append(article)
    if 'authors' in article and 'year' in article:
        info = f"**From {article['authors']}, {article['year']}** ({article['doi']}): {article['text']}"
    else:
        citation = ""
        if 'citation' in article and article['citation']:
            citation = article['citation'][0]
        info = f"**From {citation}** ({article['doi']}): {article['text']}"

    # check if info is in the messages to interface content
    if info not in [message['content'] for message in st.session_state.messages_to_interface]:
        st.session_state.messages_to_interface.append({"role": "user", "content": info})
        st.session_state.messages_to_api.append({"role": "user", "content": info})
    st.toast(f"**Added to 📚 literature review!**", icon="✅")


# remove from notes
def remove_from_lit_review(article):
    # remove article from lit review studies
    st.session_state.review_pieces.remove(article)
    if 'authors' in article and 'year' in article:
        info = f"**From {article['authors']}, {article['year']}** ({article['doi']}): {article['text']}"
    else:
        citation = ""
        if 'citation' in article and article['citation']:
            citation = article['citation'][0]
        info = f"**From {citation}** ({article['doi']}): {article['text']}"

    # check if info is in the messages to interface content
    if info in [message['content'] for message in st.session_state.messages_to_interface]:
        st.session_state.messages_to_interface.remove({"role": "user", "content": info})
        st.session_state.messages_to_api.remove({"role": "user", "content": info})
    st.toast(f"**Removed from 📚 literature review!**", icon="❌")
