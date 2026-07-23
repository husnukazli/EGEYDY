import io
import streamlit as st
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

def get_drive_service():
    """Streamlit Secrets kullanarak Google Drive servisine bağlanır."""
    creds = Credentials(
        token=None,
        refresh_token=st.secrets["refresh_token"],
        client_id=st.secrets["client_id"],
        client_secret=st.secrets["client_secret"],
        token_uri="https://oauth2.googleapis.com/token"
    )
    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(file_bytes, file_name, folder_id=None, mime_type="application/octet-stream"):
    """Dosyayı Google Drive üzerine yükler."""
    service = get_drive_service()
    
    file_metadata = {'name': file_name}
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes),
        mimetype=mime_type,
        resumable=True
    )
    
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    return uploaded_file

def list_files_in_folder(folder_id=None):
    """Belirtilen klasördeki dosyaları listeler."""
    service = get_drive_service()
    query = f"'{folder_id}' in parents and trashed = false" if folder_id else "trashed = false"
    
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="files(id, name, webViewLink, mimeType)"
    ).execute()
    
    return results.get('files', [])
