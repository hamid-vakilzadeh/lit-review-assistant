import streamlit as st


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
    if 'authors' in article and 'year' in article:
        info = f"**From {article['authors']}, {article['year']}** ({article['doi']}): {article['text']}"
        interface_context = f"**{article['authors']}, {article['year']}** ({article['doi']})"
    else:
        citation = ""
        if 'citation' in article and article['citation']:
            citation = article['citation'][0]
        info = f"**From {citation}** ({article['doi']}): {article['text']}"
        interface_context = f"**{citation}** ({article['doi']})"
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
    st.toast(f"**Added to 📚 literature review!**", icon="✅")


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
