import os
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# Google Drive API yetki kapsamı
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_drive():
    """Servis hesabı ile Google Drive API'ye bağlanır."""
    if os.path.exists('service_account.json'):
        creds = service_account.Credentials.from_service_account_file(
            'service_account.json', scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    else:
        raise FileNotFoundError("Hata: service_account.json dosyası bulunamadı.")

def upload_file_to_drive(file_bytes, file_name, folder_id):
    """Gelen dosya baytlarını belirtilen Drive klasörüne yükler."""
    service = authenticate_drive()
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    # Dosya içeriğini akış olarak hazırlarız
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype='application/octet-stream', resumable=True)
    
    # Yükleme işlemini gerçekleştiririz
    uploaded_file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, webViewLink'
    ).execute()
    
    return uploaded_file

def list_files_in_folder(folder_id):
    """Belirtilen Drive klasöründeki silinmemiş dosyaları listeler."""
    service = authenticate_drive()
    query = f"'{folder_id}' in parents and trashed = false"
    
    results = service.files().list(
        q=query,
        fields="files(id, name, webViewLink, createdTime)"
    ).execute()
    
    return results.get('files', [])
