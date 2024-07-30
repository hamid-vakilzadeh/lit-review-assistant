import streamlit as st
from utils.firestore_db import update_profile_db, update_password
from time import time


def profile():
    update_profile, change_password = st.tabs(["Update Profile", "Change Password"])

    with update_profile:
        with st.form(key='Update Profile'):
            st.markdown('### Update Profile')
            title_options = ['', 'Mr', 'Mrs', 'Ms', 'Dr', 'Prof']
            position_options = ['', 'Professor', 'Research Assistant', 'Practice', 'Student', 'Other']
            # create 3 columns
            col1, col2, col3 = st.columns([2, 5, 7])

            title = col1.selectbox(
                label='Title',
                options=title_options,
                index=title_options.index(st.session_state.profile_details['title'])
            )
            first_name = col2.text_input(
                label='First Name',
                value=st.session_state.profile_details['first_name'],
                placeholder='First Name'
            )
            last_name = col3.text_input(
                label='Last Name',
                value=st.session_state.profile_details['last_name'],
                placeholder='Last Name'
            )

            second_col1, second_col2 = st.columns(2)
            position = second_col1.selectbox(
                label='Position',
                options=position_options,
                index=position_options.index(st.session_state.profile_details['position'])
            )
            email = second_col2.text_input(
                label='Email',
                value=st.session_state.profile_details['email']
            )

            update_button = st.form_submit_button(
                label='Update Profile',
            )

        if update_button:
            # check if email is valid
            if '@' not in email:
                st.error('Invalid email')
                st.stop()
            update_profile_db(
                username=st.session_state.user['localId'],
                _db=st.session_state.db,
                title=title,
                first_name=first_name,
                last_name=last_name,
                position=position,
                email=email
            )

            st.success('Profile updated successfully')

    with change_password:
        with st.form(key='Change Password'):
            st.markdown('### Change Password')
            password = st.text_input(label='Current Password', type='password')
            new_password = st.text_input(label='New Password', type='password')
            confirm_new_password = st.text_input(label='Confirm New Password', type='password')

            submit_button = st.form_submit_button(
                label='Change Password',
            )
        if submit_button:
            try:
                # st.write(st.session_state.user)
                st.session_state.auth.sign_in_with_email_and_password(
                    email=st.session_state.user['email'],
                    password=password
                )
                changed = update_password(
                    id_token=st.session_state.user['idToken'],
                    new_password=new_password
                )

                st.session_state.user['idToken'] = changed['idToken']
                st.session_state.user['refreshToken'] = changed['refreshToken']
                st.session_state.session_start_time = time()

                st.success('Password changed successfully')

            except Exception as e:
                error = e
                #if "INVALID_EMAIL" in str(error) or "EMAIL_NOT_FOUND" in str(error):
                #    st.error('user not found please login again.')
                #elif "INVALID_PASSWORD" in str(error) or "MISSING_PASSWORD" in str(error):
                #    st.error('current password does not match')
                #else:
                st.error(error)
                st.stop()
