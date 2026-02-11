from appwrite.client import Client
from appwrite.services.databases import Databases
from appwrite.services.storage import Storage
from appwrite.services.account import Account
from appwrite.services.users import Users
from .config import settings

class AppwriteService:
    def __init__(self):
        self.client = Client()
        self.client.set_endpoint(settings.APPWRITE_ENDPOINT)
        self.client.set_project(settings.APPWRITE_PROJECT_ID)
        self.client.set_key(settings.APPWRITE_API_KEY)
        
        self.databases = Databases(self.client)
        self.storage = Storage(self.client)
        self.users = Users(self.client) # Server-side user management

    def get_database(self):
        return self.databases

    def get_storage(self):
        return self.storage
    
    def get_users(self):
        return self.users

# Singleton instance
appwrite_service = AppwriteService()
