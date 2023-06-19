import streamlit as st
from tabs import article_search, literature_review, pdf_search
from streamlit_pills import pills


def choose_model():
    # Choose the model to use for generating the response
    chosen_model = pills(
        label='Model Name',
        options=['GPT-3.5', 'GPT-3.5 16K', 'GPT-4', 'GPT-4 32K'],
    )

    if chosen_model == 'GPT-3.5':
        st.session_state.selected_model = 'gpt-3.5-turbo'
    if chosen_model == 'GPT-4':
        st.session_state.selected_model = 'gpt-4'
    if chosen_model == 'GPT-3.5 16K':
        st.session_state.selected_model = 'gpt-3.5-turbo-16k'
    if chosen_model == 'GPT-4 32K':
        st.session_state.selected_model = 'gpt-4-32k'


if __name__ == '__main__':
    # make page wide
    st.set_page_config(
        layout="wide",
        page_title="AI Research Assistant",
        page_icon="📚",
    )

    header_column1, header_column2 = st.columns([3, 1])

    # display the header and general settings
    with st.container():
        # The header
        with header_column1:
            st.header("AI Assistant: helps with accounting research")

        sub_column1, sub_column2, sub_column3, sub_column4 = st.columns(4)

        # choice of the model to use
        with sub_column1:
            choose_model()

        # Model creativity measured by temperature
        with sub_column2:
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
        with sub_column3:
            st.slider(
                label="**Response Cutoff** (in words)",
                min_value=100,
                max_value=20000,
                value=300,
                step=10,
                key="max_words",
                help="The actual response length may vary. "
                     "This helps the model to generate a response of the desired length. "
                     "But it may also result in incomplete sentences."
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

    # display the cost card
    with header_column2:
        # display the cost of total accumulated cost
        if 'total_token_cost' in st.session_state:
            st.metric(
                label="Estimated Cost",
                help="Cost is estimated based on the number of tokens used.",
                value=f"${st.session_state.total_token_cost:.4f}",
                delta=f"${st.session_state.total_token_cost - st.session_state.last_token_cost:.4f}"
            )
    # st.write(st.session_state)
