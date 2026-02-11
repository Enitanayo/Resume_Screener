import os
import time
from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.permission import Permission
from dotenv import load_dotenv

# Load env from .env file (parent dir of scripts usually, or root)
# Assuming running from root
load_dotenv()

APPWRITE_ENDPOINT = os.getenv("APPWRITE_ENDPOINT", "https://cloud.appwrite.io/v1")
APPWRITE_PROJECT_ID = os.getenv("APPWRITE_PROJECT_ID")
APPWRITE_API_KEY = os.getenv("APPWRITE_API_KEY")

if not APPWRITE_PROJECT_ID or not APPWRITE_API_KEY:
    print("Error: APPWRITE_PROJECT_ID and APPWRITE_API_KEY must be set.")
    exit(1)

client = Client()
client.set_endpoint(APPWRITE_ENDPOINT)
client.set_project(APPWRITE_PROJECT_ID)
client.set_key(APPWRITE_API_KEY)

databases = Databases(client)
storage = Storage(client)

DATABASE_ID = "default"
JOBS_COLLECTION_ID = "jobs"
CANDIDATES_COLLECTION_ID = "candidates"
APPLICATIONS_COLLECTION_ID = "applications"
RESUMES_BUCKET_ID = "resumes"

def setup_database():
    print(f"Setting up Database: {DATABASE_ID}")
    try:
        databases.get(DATABASE_ID)
        print("Database exists.")
    except Exception:
        print("Creating database...")
        databases.create(DATABASE_ID, "Default DB")

    # --- Jobs Collection ---
    setup_collection(JOBS_COLLECTION_ID, "Jobs")
    create_attribute(JOBS_COLLECTION_ID, "title", "string", 255, True)
    create_attribute(JOBS_COLLECTION_ID, "description", "string", 10000, True)
    create_attribute(JOBS_COLLECTION_ID, "requirements", "string", 5000, False)
    create_attribute(JOBS_COLLECTION_ID, "recruiter_id", "string", 255, True)
    create_attribute(JOBS_COLLECTION_ID, "is_active", "boolean", required=False, default=True)

    # --- Candidates Collection ---
    setup_collection(CANDIDATES_COLLECTION_ID, "Candidates")
    create_attribute(CANDIDATES_COLLECTION_ID, "name", "string", 255, False)
    create_attribute(CANDIDATES_COLLECTION_ID, "email", "string", 255, True) # Making email required/indexed?
    create_attribute(CANDIDATES_COLLECTION_ID, "phone", "string", 50, False)
    create_attribute(CANDIDATES_COLLECTION_ID, "skills", "string", 100000, False, array=True) # Array of strings
    create_attribute(CANDIDATES_COLLECTION_ID, "experience_years", "double", required=False)
    create_attribute(CANDIDATES_COLLECTION_ID, "summary", "string", 5000, False)

    # --- Applications Collection ---
    setup_collection(APPLICATIONS_COLLECTION_ID, "Applications")
    create_attribute(APPLICATIONS_COLLECTION_ID, "job_id", "string", 255, True)
    create_attribute(APPLICATIONS_COLLECTION_ID, "candidate_id", "string", 255, True)
    create_attribute(APPLICATIONS_COLLECTION_ID, "resume_file_id", "string", 255, True)
    create_attribute(APPLICATIONS_COLLECTION_ID, "status", "string", 50, True) # pending, processed, error
    create_attribute(APPLICATIONS_COLLECTION_ID, "parsed_summary", "string", 5000, False)
    create_attribute(APPLICATIONS_COLLECTION_ID, "embedding_id", "string", 255, False)
    create_attribute(APPLICATIONS_COLLECTION_ID, "batch_id", "string", 255, False)
    
    # Indexes
    create_index(APPLICATIONS_COLLECTION_ID, "idx_batch", "key", ["batch_id"])

def setup_storage():
    print(f"Setting up Storage Bucket: {RESUMES_BUCKET_ID}")
    try:
        storage.get_bucket(RESUMES_BUCKET_ID)
        print("Bucket exists.")
    except Exception:
        print("Creating bucket...")
        storage.create_bucket(RESUMES_BUCKET_ID, "Resumes", permissions=[
            Permission.read("any"), # Public read? Maybe restrict to users
            Permission.write("users")
        ], file_security=False)

def setup_collection(collection_id, name):
    try:
        databases.get_collection(DATABASE_ID, collection_id)
        print(f"Collection {name} exists.")
    except Exception:
        print(f"Creating collection {name}...")
        databases.create_collection(DATABASE_ID, collection_id, name)

def create_attribute(collection_id, key, type, size=None, required=False, default=None, array=False):
    try:
        # Check if exists (listing attributes is efficient enough)
        databases.get_attribute(DATABASE_ID, collection_id, key)
        print(f"Attribute {key} exists.")
    except Exception:
        print(f"Creating attribute {key}...")
        try:
            if type == "string":
                databases.create_string_attribute(DATABASE_ID, collection_id, key, size, required, default, array)
            elif type == "boolean":
                databases.create_boolean_attribute(DATABASE_ID, collection_id, key, required, default, array)
            elif type == "integer":
                databases.create_integer_attribute(DATABASE_ID, collection_id, key, required, min=None, max=None, default=default, array=array)
            elif type == "double":
                databases.create_float_attribute(DATABASE_ID, collection_id, key, required, min=None, max=None, default=default, array=array)
            
            # Wait a bit for attribute to be available
            time.sleep(1)
        except Exception as e:
            print(f"Failed to create attribute {key}: {e}")

def create_index(collection_id, key, type, attributes):
    try:
        databases.get_index(DATABASE_ID, collection_id, key)
        print(f"Index {key} exists.")
    except Exception:
        print(f"Creating index {key}...")
        try:
            databases.create_index(DATABASE_ID, collection_id, key, type, attributes)
            time.sleep(1)
        except Exception as e:
            print(f"Failed to create index {key}: {e}")

if __name__ == "__main__":
    setup_database()
    setup_storage()
    print("Appwrite setup complete.")
