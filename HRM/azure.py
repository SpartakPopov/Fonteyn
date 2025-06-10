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
        for user in data.get("value", []):
            user_id = user.get("id")
            groups = get_user_groups(access_token, user_id)
            user["groups"] = groups or []
            users.append(user)
        url = data.get("@odata.nextLink")
    return users

def get_user_by_id(access_token: str, user_id: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
    if response.status_code == 200:
        return response.json()
    logger.error(f"Failed to fetch user {user_id}: {response.status_code}, {response.text}")
    return None

def get_user_groups(access_token: str, user_id: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"https://graph.microsoft.com/v1.0/users/{user_id}/memberOf", headers=headers)
    if response.status_code == 200:
        groups = response.json().get("value", [])
        return [{"id": group["id"], "displayName": group.get("displayName", "Unknown Group")} for group in groups]
    logger.error(f"Failed to fetch groups for user {user_id}: {response.status_code}, {response.text}")
    return None

def get_all_groups(access_token: str):
    headers = {"Authorization": f"Bearer {access_token}"}
    groups = []
    url = "https://graph.microsoft.com/v1.0/groups"
    while url:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.error(f"Failed to fetch groups: {response.status_code}, {response.text}")
            return None
        data = response.json()
        groups.extend([{"id": group["id"], "displayName": group.get("displayName", "Unknown Group")} for group in data.get("value", [])])
        url = data.get("@odata.nextLink")
    return groups

def assign_user_to_groups(access_token: str, user_id: str, group_ids: list):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    for group_id in group_ids:
        body = {
            "@odata.id": f"https://graph.microsoft.com/v1.0/users/{user_id}"
        }
        logger.debug(f"Assigning user {user_id} to group {group_id}")
        response = requests.post(
            f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref",
            headers=headers,
            json=body
        )
        if response.status_code == 204:
            continue
        elif response.status_code == 403:
            logger.warning(f"Delegated token failed for group {group_id}, attempting with app token")
            app_token = get_app_access_token()
            if not app_token:
                logger.error("Failed to acquire app token")
                return 403, {"error": {"message": "Failed to acquire app token"}}
            headers = {"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"}
            response = requests.post(
                f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref",
                headers=headers,
                json=body
            )
            if response.status_code != 204:
                logger.error(f"Failed to assign user {user_id} to group {group_id}: {response.status_code}, {response.text}")
                return response.status_code, response.json()
    logger.info(f"User {user_id} assigned to groups {group_ids}")
    return True

def create_user(access_token: str, display_name: str, email: str, job_title: str, password: str):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
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
        return response.json()
    elif response.status_code == 403:
        logger.warning("Delegated token failed, attempting with app token")
        app_token = get_app_access_token()
        if not app_token:
            logger.error("Failed to acquire app token")
            return 403, {"error": {"message": "Failed to acquire app token"}}
        headers = {"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"}
        response = requests.post("https://graph.microsoft.com/v1.0/users", headers=headers, json=user_data)
        if response.status_code == 201:
            logger.info("User created successfully with app token")
            return response.json()
    logger.error(f"Failed to create user: {response.status_code}, {response.text}")
    return response.status_code, response.json()

def update_user(access_token: str, user_id: str, display_name: str, email: str, job_title: str):
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
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
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    logger.debug(f"Deleting user {user_id}")
    response = requests.delete(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
    if response.status_code == 204:
        logger.info(f"User {user_id} deleted successfully")
        return True
    elif response.status_code == 403:
        logger.warning(f"Delegated token failed for user deletion {user_id}, attempting with app token")
        app_token = get_app_access_token()
        if not app_token:
            logger.error("Failed to acquire app token")
            return 403, {"error": {"message": "Failed to acquire app token"}}
        headers = {"Authorization": f"Bearer {app_token}", "Content-Type": "application/json"}
        response = requests.delete(f"https://graph.microsoft.com/v1.0/users/{user_id}", headers=headers)
        if response.status_code == 204:
            logger.info(f"User {user_id} deleted successfully with app token")
            return True
    logger.error(f"Failed to delete user {user_id}: {response.status_code}, {response.text}")
    return response.status_code, response.json()