from tabs import new_interface, sidebar
from utils.session_state_vars import ensure_session_state_vars
import streamlit as st
from tabs.css import css_code

# ensure the session state variables are created
ensure_session_state_vars()

# run the css
css_code()

# Always show the main interface - no authentication required
new_interface.new_interface()
