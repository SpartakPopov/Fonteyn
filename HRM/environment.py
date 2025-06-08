import os
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
AZURE_AUTHORITY = os.getenv("AZURE_AUTHORITY")
AZURE_REDIRECT_URI = os.getenv("AZURE_REDIRECT_URI")
AZURE_SCOPE = ["User.Read", "User.Read.All", "User.ReadWrite.All", "Directory.ReadWrite.All"]