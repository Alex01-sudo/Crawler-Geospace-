from googleapiclient.discovery import build
from google.oauth2 import service_account




def get_drive_file_id_by_name(file_name: str, credentials_path: str) -> str | None:
    
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    
    service = build('drive', 'v3', credentials=creds)
    
    
    search_query = f"name = '{file_name}' and trashed = false"
    
    results = service.files().list(q=search_query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id'] 
    return None

def get_drive_folder_id_by_name(folder_name: str, credentials_path: str) -> str | None:
    
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    
    service = build('drive', 'v3', credentials=creds)
    
    
    search_query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    
    results = service.files().list(q=search_query, fields="files(id, name)").execute()
    items = results.get('files', [])
    
    if items:
        return items[0]['id'] 
    return None


def get_tif_from_drive(file_name: str, credentials_path: str) -> bytes | None:
    """
    Retrieves the content of a .tif file from Google Drive using its name.
    Returns the file content as bytes if found, otherwise None.
    """
    file_id = get_drive_file_id_by_name(file_name, credentials_path)
    print(f"File ID for '{file_name}': {file_id}")  
    if not file_id:
        print(f"File '{file_name}' not found in Google Drive.")
        return None
    
    scopes = ['https://www.googleapis.com/auth/drive.readonly']
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
    
    service = build('drive', 'v3', credentials=creds)
    
    request = service.files().get_media(fileId=file_id)
    try:
        file_content = request.execute()
        return file_content
    except Exception as e:
        print(f"Error downloading file '{file_name}': {e}")
        return None