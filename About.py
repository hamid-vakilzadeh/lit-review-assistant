import streamlit as st
from tabs import updates
from utils.session_state_vars import ensure_session_state_vars
from tabs.css import css_code


def about():
    col1, col2, col3 = st.columns([1, 3, 1])
    # display the header and general settings
    with col2:
        # The header
        st.header("AIRA: AI Research Assistant")

        # The description
        st.markdown(
            """
            This app is designed to assist researchers in finding and organizing literature.
            """
        )

        st.info("""
            In June 2023, we started AIRA, an experimental AI-powered research assistant using retrieval-augmented generation (RAG). 
                   Our goal was simple: help researchers navigate and summarize extensive academic literature through easy-to-use prompts. 
                   At that time, RAG represented cutting-edge technology that significantly simplified literature reviews.

            AI technology advanced rapidly. By the time we published the AIRA paper, we had already moved ahead with MCP—a stronger, upgraded research assistant. 
                   MCP builds on the initial AIRA idea but uses newer AI models to offer better performance, increased flexibility, and an improved researcher experience.

            Explore the original AIRA research paper, and if you use it, please cite our work. Also, be sure to check out MCP to see how far we’ve advanced since our initial release.

            📄 Read and cite the paper: [**Vakilzadeh, H., and Wood, D. A. (2025). The Development of a RAG-Based Artificial Intelligence Research Assistant (AIRA). _Journal of Information Systems. forthcoming_.**](https://doi.org/10.2308/ISYS-2024-041)
              """)

        st.success("""  
            ## How to Install AIRA in claude (aka MCP Version)?

            1. Sign up for a pro [Claude.ai](https://claude.ai) account (Claude stopped support for MCP on free accounts in early July 2025.)
            1. Sign up for a free [Smithery.ai](https://smithery.ai) account
            1. You will need to visit the homepage of the MCP on [Smithery.ai](https://smithery.ai/server/@hamid-vakilzadeh/mcpsemanticscholar)

            1. Follow the instructions in the video below to connect the MCP to you Claude.ai account
        """)
        with st.expander("MCP Demo", expanded=True):
            st.markdown("## AIRA - MCP Installation Instructions:")
            st.video(data="https://youtu.be/FkvfVS5FGjA", autoplay=False)

        with st.expander("MCP Demo", expanded=True):
            st.markdown("## AIRA - MCP Demo:")
            st.video(data="https://youtu.be/fYBmIUt10ck", autoplay=False)

        # display the instructions
        with st.expander("RAG Demo", expanded=True):
            st.markdown("## AIRA - RAG Demo:")
            st.video(data="https://youtu.be/tVrKVdSf-O8", autoplay=False)

        with st.expander("Change Log", expanded=True):
            updates.updates()


my_pages = [
    st.Page(about, title="Home", default=True, url_path="About.py"),
    st.Page("the_pages/1_AIRA App.py", title="AIRA Application"),
    st.Page("the_pages/3_Feedback.py", title="Contact Us", icon=":material/feedback:"),
]

if __name__ == "__main__":
    # make page wide
    st.set_page_config(
        layout="wide",
        page_title="AI Research Assistant",
        page_icon="📚",
    )
    # run the css
    css_code()

    # ensure the session state variables are created
    ensure_session_state_vars()

    col1, main_menu_col, research_tools_col, other_chats_col, col5 = st.columns(5)

    with main_menu_col.popover("Main Menu", use_container_width=True):
        st.page_link(
            st.Page("About.py"),
            label="Home",
            icon=":material/home:",
            use_container_width=True,
        )

        st.page_link(
            st.Page("the_pages/1_AIRA App.py"),
            label="**AIRA**",
            icon=":material/support_agent:",
            use_container_width=True,
        )

        st.page_link(
            st.Page("the_pages/3_Feedback.py"),
            label="Contact Us",
            icon=":material/feedback:",
            use_container_width=True,
        )

    pg = st.navigation(my_pages, position="hidden")

    pg.run()
