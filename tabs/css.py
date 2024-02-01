import streamlit as st


# run the css
def css_code():
    st.markdown(
        """
        <style>
        .main button[data-testid="baseButton-secondary"] {
        background-color: #aaaaaa; 
        color: white; 
        border: none;
        }
    
        .main button[data-testid="baseButton-secondary"]:hover {
        background-color: #ff6e6e;
        color: white;
        border: none;
        }
    
        .main button[data-testid="baseButton-primary"] {
        background-color: #dddddd; 
        color: gray; 
        border: none;   
        }
    
        .main button[data-testid="baseButton-primary"]:hover {
        background-color: #addaff; 
        color: #032038; 
        border: none;
        }
    
        div[data-testid="stSidebarContent"] button[data-testid="baseButton-primary"] {
        background-color: #aaaaaa; 
        color: white; 
        border: none;  
        }
    
        div[data-testid="stSidebarContent"] button[data-testid="baseButton-primary"]:hover {
        background-color: #ff6e6e; 
        color: white; 
        border: none;  
        }
    
        div[data-testid="stSidebarContent"] button[data-testid="baseButton-secondary"] {
        background-color: #dddddd; 
        color: gray; 
        border: none;  
        }
    
        div[data-testid="stSidebarContent"] button[data-testid="baseButton-secondary"]:hover {
        background-color: #addaff; 
        color: #032038; 
        border: none;  
        }
        </style>
    
        """,
        unsafe_allow_html=True
    )
