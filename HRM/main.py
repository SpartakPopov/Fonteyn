from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlencode
from starlette.middleware.sessions import SessionMiddleware
import logging
from environment import AZURE_REDIRECT_URI, AZURE_SCOPE, SECRET_KEY, AZURE_AUTHORITY, HRM_ADMIN_GROUP_ID
from azure import (
    build_msal_app,
    get_user_profile,
    get_all_users,
    create_user,
    get_user_by_id,
    update_user,
    delete_user,
    get_user_groups,
    get_all_groups,
    assign_user_to_groups,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse(url="/login/microsoft")

@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return RedirectResponse(url="/login/microsoft")

@app.get("/login/microsoft")
async def login_microsoft():
    msal_app = build_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )
    return RedirectResponse(url=auth_url)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Login failed: No code provided.", status_code=400)

    msal_app = build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )

    if "access_token" in result:
        # Use id_token_claims for both email and name
        id_token_claims = result.get("id_token_claims", {})
        user_email = id_token_claims.get("preferred_username")
        user_name = id_token_claims.get("name", "Microsoft User")
        access_token = result.get("access_token")
        profile = get_user_profile(access_token)
        logger.debug(f"User profile: {profile}")
        if not profile:
            return HTMLResponse("Failed to fetch user profile.", status_code=400)

        user_id = profile.get("id")
        groups = get_user_groups(access_token, user_id)
        if groups is None:
            return HTMLResponse("Failed to fetch user groups.", status_code=400)

        request.session["user"] = {
            "email": user_email,
            "name": profile.get("displayName", user_name),
            "jobTitle": profile.get("jobTitle", "N/A"),
            "id": user_id,
            "access_token": access_token,
            "groups": groups
        }
        logger.debug(f"Session user data: {request.session['user']}")
        return RedirectResponse(url="/dashboard", status_code=303)

    return HTMLResponse(f"Login failed: {result.get('error_description')}", status_code=400)

@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    user = request.session.get("user")
    logger.debug(f"Register GET - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if not any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])):
        raise HTTPException(status_code=403, detail="Only HRMadministrator members can access this page.")

    groups = get_all_groups(user["access_token"])
    if groups is None:
        return HTMLResponse("Failed to fetch groups.", status_code=400)

    success_message = request.session.pop("success_message", None)
    return templates.TemplateResponse("register.html", {
        "request": request,
        "error": None,
        "groups": groups,
        "success_message": success_message
    })

@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    group_ids: list[str] = Form(None)
):
    user = request.session.get("user")
    logger.debug(f"Register POST - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if not any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])):
        raise HTTPException(status_code=403, detail="Only HRMadministrator members can register users.")
    
    result = create_user(user["access_token"], display_name, email, "N/A", password)
    if isinstance(result, tuple):
        status_code, error_response = result
        error_message = error_response.get("error", {}).get("message", "Failed to register user in Entra ID.")
        logger.error(f"Registration error: {status_code} - {error_message} - Full response: {error_response}")
        groups = get_all_groups(user["access_token"]) or []
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": f"User creation failed: {error_message}", "groups": groups},
            status_code=400
        )

    new_user = result
    if group_ids:
        group_result = assign_user_to_groups(user["access_token"], new_user["id"], group_ids)
        if isinstance(group_result, tuple):
            status_code, error_response = group_result
            error_message = error_response.get("error", {}).get("message", "Failed to assign user to groups.")
            logger.error(f"Group assignment error: {status_code} - {error_message}")
            request.session["success_message"] = f"User {new_user['displayName']} created successfully, but group assignment failed."
            groups = get_all_groups(user["access_token"]) or []
            return templates.TemplateResponse(
                "register.html",
                {"request": request, "error": error_message, "groups": groups, "success_message": request.session["success_message"]},
                status_code=400
            )

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
async def edit_user_get(request: Request, user_id: str):
    user = request.session.get("user")
    logger.debug(f"Edit User GET - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if not any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])):
        raise HTTPException(status_code=403, detail="Only HRMadministrator members can edit users.")

    user_data = get_user_by_id(user["access_token"], user_id)
    if not user_data:
        return HTMLResponse("Failed to fetch user details.", status_code=400)

    return templates.TemplateResponse("edit_user.html", {
        "request": request,
        "user_id": user_id,
        "user_data": user_data,
        "error": None
    })

@app.post("/edit_user/{user_id}", response_class=HTMLResponse)
async def edit_user_post(
    request: Request,
    user_id: str,
    display_name: str = Form(...),
    email: str = Form(...),
    job_title: str = Form(...)
):
    user = request.session.get("user")
    logger.debug(f"Edit User POST - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if not any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])):
        raise HTTPException(status_code=403, detail="Only HRMadministrator members can edit users.")
    
    result = update_user(user["access_token"], user_id, display_name, email, job_title)
    if isinstance(result, tuple):
        status_code, error_response = result
        error_message = error_response.get("error", {}).get("message", "Failed to update user in Entra ID.")
        logger.error(f"Update error: {status_code} - {error_message} - Full response: {error_response}")
        user_data = get_user_by_id(user["access_token"], user_id) or {
            "displayName": display_name,
            "userPrincipalName": email,
            "jobTitle": job_title
        }
        return templates.TemplateResponse(
            "edit_user.html",
            {
                "request": request,
                "user_id": user_id,
                "user_data": user_data,
                "error": error_message
            },
            status_code=400
        )

    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/delete_user/{user_id}", response_class=RedirectResponse)
async def delete_user_post(request: Request, user_id: str):
    user = request.session.get("user")
    logger.debug(f"Delete User POST - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if not any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])):
        raise HTTPException(status_code=403, detail="Only HRMadministrator members can delete users.")
    
    if user_id == user["id"]:
        request.session["error_message"] = "Cannot delete your own account."
        return RedirectResponse(url="/dashboard", status_code=303)

    result = delete_user(user["access_token"], user_id)
    if isinstance(result, tuple):
        status_code, error_response = result
        error_message = error_response.get("error", {}).get("message", "Failed to delete user in Entra ID.")
        logger.error(f"Delete error: {status_code} - {error_message} - Full response: {error_response}")
        request.session["error_message"] = f"Failed to delete user: {error_message}"
        return RedirectResponse(url="/dashboard", status_code=303)

    request.session["success_message"] = "User deleted successfully."
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)

    users = get_all_users(user["access_token"])
    if not users:
        return HTMLResponse("Failed to fetch users from Entra ID.", status_code=400)

    employees = [
        (
            user["id"],
            user.get("displayName", "N/A"),
            user.get("userPrincipalName", "N/A"),
            ", ".join(group["displayName"] for group in user.get("groups", [])) or "None"
        )
        for user in users
    ]

    success_message = request.session.pop("success_message", None)
    error_message = request.session.pop("error_message", None)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["email"],
        "employees": employees,
        "is_hrm_admin": any(group["id"] == HRM_ADMIN_GROUP_ID for group in user.get("groups", [])),
        "success_message": success_message,
        "error_message": error_message
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    tenant = AZURE_AUTHORITY.split('/')[-1]
    post_logout_redirect_uri = "http://localhost:8000/login"
    params = urlencode({"post_logout_redirect_uri": post_logout_redirect_uri})
    azure_logout_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?{params}"
    return RedirectResponse(url=azure_logout_url)