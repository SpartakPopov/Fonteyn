import requests
import logging
from msal import ConfidentialClientApplication
from environment import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_AUTHORITY

logger = logging.getLogger(__name__)

def build_msal_app():
    return ConfidentialClientApplication(
        AZURE_CLIENT_ID,
        authority=AZURE_AUTHORITY,
        client_credential=AZURE_CLIENT_SECRET
    )

def get_app_access_token():
    msal_app = build_msal_app()
    result = msal_app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    if "access_token" in result:
        logger.debug(f"App access token acquired: {result['access_token'][:20]}...")
        return result["access_token"]
    logger.error(f"Failed to acquire app token: {result.get('error_description')}")
    return None

def get_user_profile(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get("https://graph.microsoft.com/v1.0/me", headers=headers)
    if response.status_code == 200:
        return response.json()
    logger.error(f"Failed to fetch user profile: {response.status_code}, {response.text}")
    return None

def get_all_users(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    users = []
    url = "https://graph.microsoft.com/v1.0/users"
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch users: {response.status_code}, {response.text}")
            return None
        data = response.json()
        users.extend(data.get("value", []))
        url = data.get("@odata.nextLink")
    return users

def get_user_by_id(access_token: str, user_id: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    logger.error(f"Failed to fetch user {user_id}: {response.status_code}, {response.text}")
    return None

def assign_directory_role(access_token: str, user_id: str, role_id: str = "fe930be7-5e62-47db-91af-98c3a49a38b1"):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    role_assignment = {
        "principalId": user_id,
        "roleDefinitionId": role_id,
        "directoryScopeId": "/"
    }
    response = requests.post(
        "https://graph.microsoft.com/v1.0/roleManagement/directory/roleAssignments",
        headers=headers,
        json=role_assignment
    )
    if response.status_code == 201:
        logger.info(f"Assigned User Administrator role to user {user_id}")
        return True
    logger.error(f"Failed to assign directory role: {response.status_code}, {response.text}")
    return False

def create_user(access_token: str, display_name: str, email: str, job_title: str, password: str, is_admin: bool = False):
    app_token = get_app_access_token()
    if not app_token:
        return 403, {"error": {"message": "Failed to acquire app token"}}
    
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Content-Type": "application/json"
    }
    user_data = {
        "accountEnabled": True,
        "displayName": display_name,
        "mailNickname": email.split("@")[0],
        "userPrincipalName": email,
        "jobTitle": job_title,
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": password
        }
    }
    logger.debug(f"Creating user with data: {user_data}")
    response = requests.post("https://graph.microsoft.com/v1.0/users", headers=headers, json=user_data)
    if response.status_code == 201:
        logger.info("User created successfully")
        user = response.json()
        if is_admin:
            success = assign_directory_role(app_token, user["id"])
            if not success:
                logger.warning("User created but failed to assign admin role")
        return user
    logger.error(f"Failed to create user: {response.status_code}, {response.text}")
    return response.status_code, response.json()

def update_user(access_token: str, user_id: str, display_name: str, email: str, job_title: str):
    app_token = get_app_access_token()
    if not app_token:
        return 403, {"error": {"message": "Failed to acquire app token"}}
    
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Content-Type": "application/json"
    }
    user_data = {
        "displayName": display_name,
        "userPrincipalName": email,
        "jobTitle": job_title
    }
    logger.debug(f"Updating user {user_id} with data: {user_data}")
    response = requests.patch(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers, json=user_data)
    if response.status_code == 204:
        logger.info(f"User {user_id} updated successfully")
        return True
    logger.error(f"Failed to update user {user_id}: {response.status_code}, {response.text}")
    return response.status_code, response.json()

def delete_user(access_token: str, user_id: str):
    app_token = get_app_access_token()
    if not app_token:
        return 403, {"error": {"message": "Failed to acquire app token"}}
    
    headers = {
        "Authorization": f"Bearer {app_token}",
        "Content-Type": "application/json"
    }
    logger.debug(f"Deleting user {user_id}")
    response = requests.delete(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
    if response.status_code == 204:
        logger.info(f"User {user_id} deleted successfully")
        return True
    logger.error(f"Failed to delete user {user_id}: {response.status_code}, {response.text}")
    return response.status_code, response.json()