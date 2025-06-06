from utils.session_state_vars import ensure_session_state_vars
import streamlit as st
from tabs.css import css_code

# ensure the session state variables are created
ensure_session_state_vars()

# run the css
css_code()


def feedback_session():
    col1, col2, col3 = st.columns([1, 3, 1])

    col2.markdown(
        """
        ## Contact Us

        If you have any questions or require further information, please do not hesitate to reach out to us.
        We sincerely appreciate your time and input. Thank you for contributing to the improvement of the AI Research Assistant.
        """
    )
    with col2:
        col1, hamid, david, col4 = st.columns([1, 2, 2, 1], vertical_alignment='center', gap='large')
        with hamid:
            st.image(
                image='public/image/hamid-vakilzadeh.jpeg',
                caption='Hamid Vakilzadeh',
            )
            st.markdown("""                                        
                            <style>
                                .libutton {
                                display: flex;
                                flex-direction: column;
                                justify-content: center;
                                padding: 7px;
                                text-align: center;
                                outline: none;
                                text-decoration: none !important;
                                color: #ffffff !important;
                                width: 200px;
                                height: 32px;
                                border-radius: 16px;
                                background-color: #0A66C2;
                                font-family: "SF Pro Text", Helvetica, sans-serif;
                                }
                            </style>
                        <a class="libutton" href="https://www.linkedin.com/comm/mynetwork/discovery-see-all?usecase=PEOPLE_FOLLOWS&followMember=hamid-vakilzadeh" target="_blank">Follow on LinkedIn</a>
                        """, unsafe_allow_html=True)

        with david:
            st.image(
                image='public/image/david-wood.jpeg',
                caption='David A. Wood',
            )
            st.markdown("""                                        
                            <style>
                                .libutton {
                                display: flex;
                                flex-direction: column;
                                justify-content: center;
                                padding: 7px;
                                text-align: center;
                                outline: none;
                                text-decoration: none !important;
                                color: #ffffff !important;
                                width: 200px;
                                height: 32px;
                                border-radius: 16px;
                                background-color: #0A66C2;
                                font-family: "SF Pro Text", Helvetica, sans-serif;
                                }
                            </style>
                        <a class="libutton" href="https://www.linkedin.com/in/davidawood/" target="_blank">Follow on LinkedIn</a>
                        """, unsafe_allow_html=True)


# Always show feedback - no authentication required
feedback_session()
