import firebase_admin
from firebase_admin import credentials, firestore
from pathlib import Path
import shutil
from datetime import datetime, timezone

DEFAULT_CREDENTIALS_PATH = Path.home() / '.console_capture' / 'service_account.json'

def get_valid_credentials_path():
    if DEFAULT_CREDENTIALS_PATH.exists():
        try:
            initialize_firebase(str(DEFAULT_CREDENTIALS_PATH))
            return str(DEFAULT_CREDENTIALS_PATH)
        except Exception:
            print(f"Existing credentials at {DEFAULT_CREDENTIALS_PATH} are invalid.")
    
    while True:
        user_path = input("Enter the path to your service account JSON file: ").strip()
        if not user_path:
            raise ValueError("No service account file provided.")
        
        try:
            initialize_firebase(user_path)
            DEFAULT_CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(user_path, DEFAULT_CREDENTIALS_PATH)
            print(f"Credentials copied to {DEFAULT_CREDENTIALS_PATH}")
            return str(DEFAULT_CREDENTIALS_PATH)
        except Exception as e:
            print(f"Invalid credentials file: {e}")

def initialize_firebase(key_path):
    cred = credentials.Certificate(key_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    return firestore.client()

def send_to_firebase(db, stream_id, lines, index, lock):
    with lock:
        try:
            db.collection('console_output').document(stream_id).collection('lines').add({
                'timestamp': datetime.now(timezone.utc),
                'output': [{"timestamp": line[0], "line": line[1]} for line in lines],
                'index': index
            })
            lines.clear()
        except Exception as e:
            return None

def create_firebase_stream(db, title):
    try:
        _, doc_ref = db.collection('console_output').add({
            'title': title,
            'timestamp': datetime.now(timezone.utc)
        })
        return doc_ref.id
    except Exception as e:
        print(f"Error creating Firebase stream: {e}")
        return None