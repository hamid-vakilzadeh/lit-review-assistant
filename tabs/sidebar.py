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


def choose_model():
    # Choose the model to use for generating the response
    chosen_model = st.selectbox(
        label='Model Name',
        options=[
            'OpenAI: GPT-3.5 16K',
            'OpenAI: GPT-4 32K',
            'Google: PaLM 2 Bison',
            'Anthropic: Claude v2',
            'Anthropic: Claude Instant v1',
            'Meta: Llama v2 13B Chat',
            'Meta: Llama v2 70B Chat',
                 ],
    )

    if chosen_model == 'OpenAI: GPT-3.5 16K':
        st.session_state.selected_model = 'openai/gpt-3.5-turbo-16k'
    if chosen_model == 'OpenAI: GPT-4 32K':
        st.session_state.selected_model = 'openai/gpt-4-32k'
    if chosen_model == 'Google: PaLM 2 Bison':
        st.session_state.selected_model = 'google/palm-2-chat-bison'
    if chosen_model == 'Anthropic: Claude v2':
        st.session_state.selected_model = 'anthropic/claude-2'
    if chosen_model == 'Anthropic: Claude Instant v1':
        st.session_state.selected_model = 'anthropic/claude-instant-v1'
    if chosen_model == 'Meta: Llama v2 13B Chat':
        st.session_state.selected_model = 'meta-llama/llama-2-13b-chat'
    if chosen_model == 'Meta: Llama v2 70B Chat':
        st.session_state.selected_model = 'meta-llama/llama-2-70b-chat'


def show_sidebar():
    # sidebar
    with st.sidebar:
        choose_model()
        st.header("📌 My Pinboard")
        st.markdown("You can keep track of abstract, summaries, and reviews "
                    "that you pin while you are reviewing the literature. "
                    )
        st.radio(
            label="Show Pinned:",
            options=[
                f"Abstracts: {len(st.session_state.pinned_articles)}",
                f"PDF pieces: {len(st.session_state.pinned_pdfs)}",
                f"Reviews: {len(st.session_state.pinned_reviews)}"
            ],
            key="show_pinned",
            horizontal=True,
        )
        # st.subheader(f"Selected pieces for review: {len(st.session_state.review_pieces)}")

        if st.session_state.show_pinned == f"Abstracts: {len(st.session_state.pinned_articles)}":
            st.markdown("Articles that you have found in the **Articles** tab.")
            for article in st.session_state.pinned_articles:
                st.markdown(f"**{article['title']}**")
                review_action_buttons(article, st.session_state.pinned_articles)
                st.markdown(f"{article['doi'].strip()}" ,)
                st.markdown(f"{article['text']}")
                st.markdown("---")
        elif st.session_state.show_pinned == f"PDF pieces: {len(st.session_state.pinned_pdfs)}":
            st.markdown("Summaries that you have created in the **MyPDF** tab.")
            for piece in st.session_state.pinned_pdfs:
                st.markdown(f"**{piece['citation'][0].strip()}**")
                review_action_buttons(piece, st.session_state.pinned_pdfs)
                st.markdown(f"{piece['prompt']}")
                st.markdown(f"{piece['text']}")
                st.markdown("---")
        else:
            st.markdown("Reviews that you have created in the **Literature Review** tab.")
            for review in st.session_state.pinned_reviews:
                st.markdown(f"**{review['id']}**")
                review_action_buttons(review, st.session_state.pinned_reviews)
                st.markdown(f"{review['text']}")
                st.markdown("{citations}".format(citations='\n'.join(review['citation'])))
                st.markdown("---")
