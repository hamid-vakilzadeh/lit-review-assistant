from tabs import improved_interface
from utils.session_state_vars import ensure_session_state_vars
from tabs.css import css_code

# ensure the session state variables are created
ensure_session_state_vars()

# run the css
css_code()

# Always show the improved interface - no authentication required
improved_interface.improved_interface()
