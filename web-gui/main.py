import streamlit, json

credintials: dict = json.loads(open('../config.json', 'r').read())['web-app']

placeholder = streamlit.empty()

with placeholder.form("login"):
    streamlit.markdown("#### Enter your credentials")
    streamlit.markdown("The username and password is written in the json config file (`config.json`). In order to login, please use the corresponding credintials from the config files.")

    usernameInput = streamlit.text_input("Username")
    passwordInput = streamlit.text_input("Password", type = "password")
    submitButton = streamlit.form_submit_button("Login")

if submitButton and (usernameInput == credintials['username'] and passwordInput == credintials['password']):
    streamlit.session_state['credintials'] = {'username': usernameInput, 'password': passwordInput}
    placeholder.empty()

    streamlit.title('Welcome back, %s!')
