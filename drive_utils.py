import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def get_drive_service():
    # Streamlit Secrets panelinden bilgileri çekiyoruz
    creds = Credentials(
        token=None,
        refresh_token=st.secrets["refresh_token"],
        client_id=st.secrets["client_id"],
        client_secret=st.secrets["client_secret"],
        token_uri="https://oauth2.googleapis.com/token"
    )
    
    # Drive servisini oluşturup döndürüyoruz
    return build('drive', 'v3', credentials=creds)
