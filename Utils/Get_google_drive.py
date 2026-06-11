from googleapiclient.discovery import build
from google.oauth2 import service_account

def get_drive_file_id_by_name(file_name: str, credentials_path: str) -> str | None:
    """
    Queries the Google Drive API to search for a file by its exact name 
    and returns its unique Google Cloud ID.
    """
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    # Build the Drive API client
    service = build('drive', 'v3', credentials=creds)
    
    # Create an explicit search query for the file name
    search_query = f"name = '{file_name}' and trashed = false"
    
    results = service.files().list(q=search_query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id'] # This is the unique ID needed for cloud downloads
    return None