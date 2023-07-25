import streamlit as st
from tabs import article_search, literature_review, pdf_search
from streamlit_pills import pills
from tabs.session_state_vars import ensure_session_state_vars

# ensure the session state variables are created
ensure_session_state_vars()


def choose_model():
    # Choose the model to use for generating the response
    chosen_model = pills(
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


if __name__ == '__main__':
    # make page wide
    st.set_page_config(
        layout="centered",
        page_title="AI Research Assistant",
        page_icon="📚",
    )

    # display the header and general settings
    with st.container():
        # The header
        st.header("AI Assistant for accounting research")

        # choice of the model to use
        choose_model()

        # create 3 columns
        sub_column1, sub_column2 = st.columns(2)

        # first column shows model creativity measured by temperature
        with sub_column1:
            st.slider(
                label="**Model Creativity** (aka temperature)",
                min_value=0.0,
                max_value=1.0,
                value=0.3,
                step=0.1,
                key="temperature",
                help="The higher the temperature,"
                     " the more creative the model will be. "
                     "However, the model may also generate "
                     "gibberish when the temperature is high."
            )

        # specify the desired length of the response
        with sub_column2:
            st.slider(
                label="**Response Cutoff** (in words)",
                min_value=100,
                max_value=20000,
                value=300,
                step=10,
                key="max_words",
                help="The actual response length may vary. "
            )

    article_search_tab, pdf_tab, literature_review_tab = st.tabs(
        ["**Articles**", "**My PDFs**", "**Literature Review**"]
    )

    # display the Articles Search tab
    with article_search_tab:
        article_search.article_search()

    # display the PDF Search (My PDFs) tab
    with pdf_tab:
        pdf_search.pdf_search()

    # display the Literature Review tab
    with literature_review_tab:
        literature_review.literature_review()
