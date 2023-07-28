import streamlit as st
from utils.funcs import show_pin_buttons


def review_action_buttons(article, state_var):
    # create 2 columns for the buttons
    col1, col2 = st.columns(2)
    with col1:
        if article not in st.session_state.review_pieces:
            # include in lit review button
            st.button(
                label="✅ Include in Lit Review",
                type="primary",
                use_container_width=True,
                key=f"include_{article['id']}",
                on_click=add_to_lit_review,
                args=(article,)
            )
        else:
            # remove from lit review button
            st.button(
                label="❌ Remove from Lit Review",
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
def add_to_lit_review(paper):
    # add article to lit review studies
    st.session_state.review_pieces.append(paper)
    st.toast(f"**Added to 📚 literature review!**", icon="✅")


# remove from notes
def remove_from_lit_review(paper):
    # remove article from lit review studies
    st.session_state.review_pieces.remove(paper)
    st.toast(f"**Removed from 📚 literature review!**", icon="❌")


def show_sidebar():
    # sidebar
    with st.sidebar:
        st.header("📌 My Pinboard")
        st.markdown("You can keep track of abstract, summaries, and reviews "
                    "that you pin while you are reviewing the literature. "
                    )
        st.write(f"Pinned Abstracts: **{len(st.session_state.pinned_articles)}**")
        st.write(f"Pinned PDF pieces: **{len(st.session_state.pinned_pdfs)}**")
        st.write(f"Pinned Reviews: **{len(st.session_state.previous_reviews)}**")

        st.markdown("You can also select pieces to include in your literature review.")
        st.subheader(f"Selected pieces for review: {len(st.session_state.review_pieces)}")

        # show dropdown menu to choose articles or pdfs
        st.selectbox(
            label="Select an option to review",
            options=["Articles", "PDFs", "Reviews"],
            key="articles_or_notes",
            index=0
        )

        if st.session_state.articles_or_notes == "Articles":
            st.markdown("Articles that you have found in the **Articles** tab.")
            for article in st.session_state.pinned_articles:
                st.markdown(f"**{article['title']}**")
                review_action_buttons(article, st.session_state.pinned_articles)
                st.markdown(f"{article['doi'].strip()}" ,)
                st.markdown(f"{article['text']}")
                st.markdown("---")
        elif st.session_state.articles_or_notes == "PDFs":
            st.markdown("Summaries that you have created in the **MyPDF** tab.")
            for piece in st.session_state.pinned_pdfs:
                st.markdown(f"**{piece['citation'].strip()}**")
                review_action_buttons(piece, st.session_state.pinned_pdfs)
                st.markdown(f"{piece['prompt']}")
                st.markdown(f"{piece['text']}")
                st.markdown("---")
        else:
            st.markdown("Reviews that you have created in the **Literature Review** tab.")
