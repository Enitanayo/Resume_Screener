import os
import sys
# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from appwrite.client import Client
from appwrite.services.databases import Databases
from qdrant_client import QdrantClient
from dotenv import load_dotenv

load_dotenv()

def check_status():
    # 1. Check Qdrant
    print("--- Qdrant Status ---")
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant_key = os.getenv("QDRANT_API_KEY", "")
        qdrant = QdrantClient(url=qdrant_url, api_key=qdrant_key)
        try:
            res = qdrant.get_collection("candidates")
            # Qdrant client 1.x: res is CollectionInfo
            # res.vectors_count might be nested or named points_count
            print(f"Collection 'candidates' exists.")
            print(f"Points Count: {res.points_count}")
            if res.points_count == 0:
                print("WARNING: Collection is empty. No candidates can be matched.")
        except Exception as e:
            print(f"Collection 'candidates' not found or error: {e}")
    except Exception as e:
        print(f"Failed to connect to Qdrant: {e}")

    # 2. Check Appwrite Applications
    print("\n--- Appwrite Applications Status ---")
    try:
        endpoint = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
        project = os.getenv("APPWRITE_PROJECT_ID")
        key = os.getenv("APPWRITE_API_KEY")
        
        if not project or not key:
             print("Error: Missing APPWRITE_PROJECT_ID or APPWRITE_API_KEY in .env")
             return

        client = Client()
        client.set_endpoint(endpoint)
        client.set_project(project)
        client.set_key(key)
        
        db = Databases(client)
        db_id = os.getenv("DATABASE_ID", "default")
        coll_id = os.getenv("APPLICATIONS_COLLECTION_ID", "applications")
        
        res = db.list_documents(db_id, coll_id)
        total = res['total']
        print(f"Total Applications: {total}")
        
        statuses = {}
        for doc in res['documents']:
            s = doc.get('status', 'unknown')
            statuses[s] = statuses.get(s, 0) + 1
            
        for s, count in statuses.items():
            print(f"  - {s}: {count}")
            
        if statuses.get('processed', 0) == 0 and total > 0:
             print("WARNING: No applications are processed. This explains why no candidates are matched.")
             
    except Exception as e:
        print(f"Failed to connect to Appwrite: {e}")

if __name__ == "__main__":
    check_status()
