from tabs import new_interface, sidebar
from utils.session_state_vars import ensure_session_state_vars

# ensure the session state variables are created
ensure_session_state_vars()


if __name__ == '__main__':

    new_interface.new_interface()
