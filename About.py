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
            **Two Years of AIRA: From RAG to MCP**

            In June 2023, we started AIRA, an experimental AI-powered research assistant using retrieval-augmented generation (RAG). 
                   Our goal was simple: help researchers navigate and summarize extensive academic literature through easy-to-use prompts. 
                   At that time, RAG represented cutting-edge technology that significantly simplified literature reviews.

            AI technology advanced rapidly. By the time we published the AIRA paper, we had already moved ahead with MCP—a stronger, upgraded research assistant. 
                   MCP builds on the initial AIRA idea but uses newer AI models to offer better performance, increased flexibility, and an improved researcher experience.

            Explore the original AIRA research paper, and if you use it, please cite our work. Also, be sure to check out MCP to see how far we’ve advanced since our initial release.

            📄 Read and cite the paper: **Vakilzadeh, H., and Wood, D. A. (2025). The Development of a RAG-Based Artificial Intelligence Research Assistant (AIRA). _Journal of Information Systems. forthcoming_.**
              """)
        
        st.success("""  
            **How to Install MCP?**

            First, make sure you've downloaded and installed the [Claude Desktop](https://claude.ai/download) app and you have [npm](http://nodejs.org/) installed.

            To install this MCP Server via [Smithery](https://smithery.ai/server/@hamid-vakilzadeh/mcpsemanticscholar) open your terminal/CMD and run the following command:

                npx -y @smithery/cli@latest install @hamid-vakilzadeh/mcpsemanticscholar --client claude
            
            Finally, restart Claude Desktop and the MCP should apper in search and tools.

            > **Note:**
            > 
            > **The API allows up to 100 requests per 5 minutes. To access a higher rate limit, visit Semantic Scholar to request authentication for your project.**
            
            Learn more about the MCP project on [GitHub](https://github.com/hamid-vakilzadeh/AIRA-SemanticScholar)
        """)

        # display the instructions
        with st.expander("Instructions", expanded=True):
            st.video(
                data="https://youtu.be/tVrKVdSf-O8",
                autoplay=False
            )

        with st.expander("Change Log", expanded=True):
            updates.updates()


my_pages = [
    st.Page(about, title='Home', default=True, url_path='About.py'),
    st.Page("the_pages/1_AIRA App.py", title='AIRA Application'),
    st.Page("the_pages/3_Feedback.py", title="Feedback"),
]

if __name__ == '__main__':

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
            label="Feedback",
            icon=":material/feedback:",
            use_container_width=True,
        )

    pg = st.navigation(my_pages, position='hidden')


    pg.run()
