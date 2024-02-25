from tabs import profile, sidebar
from utils.session_state_vars import ensure_session_state_vars
import streamlit as st
from tabs.css import css_code
# ensure the session state variables are created
ensure_session_state_vars()

# run the css
css_code()


def feedback_session():
    st.markdown(
        """
        **We Value Your Feedback**

        Thank you for utilizing the AI Research Assistant. Your input is invaluable to us, and we kindly invite you to share your experience 
        by participating in a brief survey. Your feedback is crucial as it will not only contribute to our ongoing research publication but 
        also guide us in enhancing this tool for future users.

        **Please Complete Our Survey**

        Your insights are important, and completing the survey will only take a few minutes of your time. 
        To ensure we gather your feedback efficiently, we will send one reminder email before the deadline. 
        We aim to make the AI Research Assistant as user-friendly and effective as possible, 
        and your feedback is a vital part of this process.
        """)

    st.link_button(
        label="**Start Survey**",
        url="https://byu.az1.qualtrics.com/jfe/form/SV_7Q9B81oKDYM9YTs",
        use_container_width=True,
        type="primary"
        )

    st.markdown(
        """
        Alternatively, you can copy and paste the URL below into your web browser:
        ```
        https://byu.az1.qualtrics.com/jfe/form/SV_7Q9B81oKDYM9YTs
        ```

        **Contact Us**

        Should you have any questions or require further information, please do not hesitate to reach out to us.
        We sincerely appreciate your time and input. Thank you for contributing to the improvement of the AI Research Assistant.
        """
    )
    hamid, david = st.columns(2)
    with hamid:
        st.markdown("[**Hamid Vakilzadeh**](https://www.linkedin.com/in/hamid-vakilzadeh/)")
        st.link_button("Contact", "mailto:vakilzas@uww.edu", type="primary")
    with david:
        st.markdown("[**David A. Wood**](https://www.linkedin.com/in/davidawood/)")
        st.link_button("Contact", "mailto:davidwood@byu.edu", type="primary")


if __name__ == '__main__':
    if 'user' not in st.session_state:
        sidebar.login_and_reset_password()

    else:
        with st.sidebar:
            sidebar.show_logout()
        feedback_session()
