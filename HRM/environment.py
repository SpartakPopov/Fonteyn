import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_AUTHORITY = os.getenv("AZURE_AUTHORITY")
AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI")
AZURE_SCOPE = [os.getenv("AZURE_SCOPE", "User.Read")]
