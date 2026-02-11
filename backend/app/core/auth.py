from fastapi import Header, HTTPException, status, Depends
from appwrite.client import Client
from appwrite.services.account import Account
from .config import settings
from typing import Optional

async def get_current_user(x_appwrite_jwt: Optional[str] = Header(None)):
    if not x_appwrite_jwt:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
        )
    
    # Initialize a new client for the user (not server) to verify session
    client = Client()
    client.set_endpoint(settings.APPWRITE_ENDPOINT)
    client.set_project(settings.APPWRITE_PROJECT_ID)
    client.set_jwt(x_appwrite_jwt)
    
    account = Account(client)
    try:
        user = account.get()
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

def require_recruiter(user: dict = Depends(get_current_user)):
    # Check if user has 'recruiter' label or role
    # Assuming roles are in labels or a custom preference
    # For now, let's assume a label 'recruiter'
    if 'recruiter' not in user.get('labels', []):
         raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Recruiter role required",
        )
    return user

def require_candidate(user: dict = Depends(get_current_user)):
    # Basic check, any auth user can be candidate? 
    # Or strict 'candidate' label?
    # Let's assume default is candidate unless specified.
    return user
