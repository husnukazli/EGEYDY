import os
import io
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_drive():
    """
    Lokalde 'service_account.json' dosyasından,
    Streamlit Cloud'da 'st.secrets["service_account_json"]' alanından okuma yapar.
    """
    creds = None
    
    # 1. Yerel bilgisayar kontrolü (dosya varsa)
    if os.path.exists('service_account.json'):
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES
        )
    # 2. Streamlit Cloud Secrets kontrolü (üç tırnak arası metin)
    elif "service_account_json" in st.secrets:
        # Metin olarak gelen JSON'ı sözlüğe (dict) dönüştürürüz
        creds_dict = json.loads(st.secrets["service_account_json"])
        creds = service_account.Credentials.from_service_account_info(
            creds_dict, scopes=SCOPES
        )
    else:
        raise FileNotFoundError(
            "Hata: Ne yerel service_account.json ne de Streamlit Secrets bilgisi bulunamadı!"
        )

    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_bytes, file_name, folder_id):
    service = authenticate_drive()
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes), 
        mimetype='application/octet-stream', 
        resumable=True
    )
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    return uploaded_file

def list_files_in_folder(folder_id):
    service = authenticate_drive()
    query = f"'{folder_id}' in parents and trashed = false"
    
    results = service.files().list(
        q=query,
        fields="files(id, name, webViewLink, createdTime)"
    ).execute()
    
    return results.get('files', [])
