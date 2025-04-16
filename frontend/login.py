import sys
import streamlit as st
import requests
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from monitor import WildlifeMonitor

BASE_URL = "http://127.0.0.1:8000/api/accounts/"

def register():
    st.title("Register")
    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Register"):
        response = requests.post(f"{BASE_URL}register/", json={
            "username": username,
            "email": email,
            "password": password
        })

        if response.status_code == 201:
            st.success("✅ Registration successful! Please log in.")
            st.session_state["registered"] = True  # ✅ Store in session
        else:
            st.error(response.json().get("error", "❌ Registration failed"))

    # ✅ If registration is successful, show a login button
    if st.session_state.get("registered"):
        if st.button("Go to Login"):
            st.session_state["page"] = "login"
            st.rerun()

def login():
    st.title("Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        response = requests.post(f"{BASE_URL}login/", json={"email": email, "password": password})
        
        if response.status_code == 200:
            data = response.json()
            user_email = data.get("email")  # Extract email from API response

            if user_email:
                

                st.session_state["logged_in"] = True
                st.session_state["email"] = user_email

                
                st.success(f"Login successful! Logged in as {user_email}")
                  
                # ✅ Run Streamlit app
                os.system("streamlit run frontend/app.py")
                st.stop()
            else:
                st.error("No registered email found!")
        else:
            st.error("Invalid credentials")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    option = st.radio("Choose an option:", ["Login", "Register"])
    if option == "Login":
        login()
    else:
        register()
