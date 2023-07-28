import streamlit as st


def pin_piece(piece, state_var):
    # add pieces related to the article
    state_var.append(piece)


def unpin_piece(article, state_var):
    # unpin the article
    state_var.remove(article)
    if article in st.session_state.review_pieces:
        st.session_state.review_pieces.remove(article)


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