import msal
import requests
import uuid
from flask import session, url_for, redirect, request
import os
from functools import wraps
from models import User, db
from dotenv import load_dotenv

load_dotenv()

# Entra ID Configuration
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
AUTHORITY = os.getenv('ENTRA_ID_AUTHORITY', "https://login.microsoftonline.com/8c28e6dc-ec5c-42dc-9d5f-0be7fa070508")
REDIRECT_URI = os.getenv('REDIRECT_URI', "https://4.209.44.134/admin/msauth")
SCOPE = [os.getenv('ENTRA_ID_SCOPE', "User.Read")]

def build_msal_app(cache=None, authority=None):
    """Build MSAL application"""
    return msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=authority or AUTHORITY,
        client_credential=CLIENT_SECRET,
        token_cache=cache
    )

def build_auth_url(authority=None, scopes=None, state=None):
    """Build authorization URL for Entra ID"""
    return build_msal_app(authority=authority).get_authorization_request_url(
        scopes or SCOPE,
        state=state or str(uuid.uuid4()),
        redirect_uri=REDIRECT_URI
    )

def get_token_from_code(auth_code, authority=None):
    """Get access token from authorization code"""
    app = build_msal_app(authority=authority)
    result = app.acquire_token_by_authorization_code(
        auth_code,
        scopes=SCOPE,
        redirect_uri=REDIRECT_URI
    )
    return result

def get_user_info(access_token):
    """Get user information from Microsoft Graph API"""
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
    if response.status_code == 200:
        return response.json()
    return None

def create_or_get_user(user_info):
    """Create or get user from database based on Microsoft account"""
    email = user_info.get('mail') or user_info.get('userPrincipalName')
    if not email:
        return None
    
    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if user:
        return user
    
    # Create new user
    user = User(
        username=user_info.get('displayName', email.split('@')[0]),
        email=email,
        password='',  # No password for Entra ID users
        is_admin=False  # Default to regular user
    )
    db.session.add(user)
    db.session.commit()
    return user

def entra_id_required(f):
    """Decorator to require Entra ID authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'entra_id_user' not in session:
            return redirect(url_for('entra_id_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_entra_id_required(f):
    """Decorator to require Entra ID authentication and admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'entra_id_user' not in session:
            return redirect(url_for('entra_id_login'))
        
        user = User.query.filter_by(email=session['entra_id_user']['email']).first()
        if not user or not user.is_admin:
            return redirect(url_for('entra_id_login'))
        
        return f(*args, **kwargs)
    return decorated_function 