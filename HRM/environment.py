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
HRM_ADMIN_GROUP_ID = os.getenv("HRM_ADMIN_GROUP_ID")
AZURE_SCOPE = [
    "https://graph.microsoft.com/User.Read",
    "https://graph.microsoft.com/User.Read.All",
    "https://graph.microsoft.com/User.ReadWrite.All",
    "https://graph.microsoft.com/GroupMember.Read.All",
    "https://graph.microsoft.com/Group.Read.All",
    "https://graph.microsoft.com/Directory.ReadWrite.All"
]
HRM_ADMIN_GROUP_ID = os.getenv("HRM_ADMIN_GROUP_ID")