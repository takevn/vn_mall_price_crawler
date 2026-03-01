"""
Script để upload file lên Google Drive từ GitHub Actions
Sử dụng Google Drive API với Service Account
"""
import os
import sys
import zipfile
from pathlib import Path
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Google Drive folder ID
FOLDER_ID = "1nKs_BQqje1WT5cOMNf0S_1Tu1gx5PnP3"

def create_zip_file(source_dir, zip_path):
    """Tạo file zip từ thư mục"""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    print(f"✅ Created zip file: {zip_path}")

def upload_to_drive(file_path, folder_id, credentials_json):
    """Upload file lên Google Drive"""
    try:
        # Load credentials từ JSON string hoặc file
        import json
        
        # Nếu là đường dẫn file, đọc file
        if os.path.isfile(credentials_json):
            with open(credentials_json, 'r', encoding='utf-8') as f:
                creds_info = json.load(f)
        else:
            # Nếu là JSON string
            creds_info = json.loads(credentials_json)
        
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        
        # Tạo service
        service = build('drive', 'v3', credentials=credentials)
        
        # Lấy tên file
        file_name = os.path.basename(file_path)
        
        # Tạo metadata
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        # Upload file
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink'
        ).execute()
        
        print(f"✅ Uploaded successfully!")
        print(f"   File ID: {file.get('id')}")
        print(f"   File Name: {file.get('name')}")
        print(f"   View Link: {file.get('webViewLink')}")
        return file
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")
        sys.exit(1)
    except Exception as error:
        print(f"❌ An error occurred: {error}")
        sys.exit(1)

def main():
    # Lấy thông tin từ environment variables
    source_dir = os.getenv('SOURCE_DIR', 'dist/Supermarket Price Crawler')
    zip_filename_base = os.getenv('ZIP_FILENAME', 'SupermarketPriceCrawler-Windows')
    credentials_json = os.getenv('GDRIVE_CREDENTIALS')
    
    if not credentials_json:
        print("⚠️  GDRIVE_CREDENTIALS environment variable not set")
        print("   Skipping Google Drive upload. Please set it in GitHub Secrets to enable upload.")
        sys.exit(0)  # Exit successfully, không fail workflow
    
    # Thêm timestamp vào tên file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"{zip_filename_base}_{timestamp}.zip"
    
    # Tạo zip file
    zip_path = zip_filename
    if os.path.isdir(source_dir):
        create_zip_file(source_dir, zip_path)
    elif os.path.isfile(source_dir):
        # Nếu là file, copy thành zip
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(source_dir, os.path.basename(source_dir))
        print(f"✅ Created zip file: {zip_path}")
    else:
        print(f"❌ Source path not found: {source_dir}")
        sys.exit(1)
    
    # Upload lên Google Drive
    print(f"\n📤 Uploading to Google Drive...")
    print(f"   Folder ID: {FOLDER_ID}")
    upload_to_drive(zip_path, FOLDER_ID, credentials_json)
    
    # Cleanup
    if os.path.exists(zip_path):
        os.remove(zip_path)
        print(f"✅ Cleaned up temporary zip file")

if __name__ == "__main__":
    main()

