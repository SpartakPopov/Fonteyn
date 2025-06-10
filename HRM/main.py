from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlencode
from starlette.middleware.sessions import SessionMiddleware
import logging
from environment import AZURE_REDIRECT_URI, AZURE_SCOPE, SECRET_KEY, AZURE_AUTHORITY
from azure import (
    build_msal_app,
    get_user_profile,
    get_all_users,
    create_user,
    get_user_by_id,
    update_user,
    delete_user,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
# mounting the static folder
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
        user_email = result.get("id_token_claims", {}).get("preferred_username")
        user_name = result.get("id_token_claims", {}).get("name", "Microsoft User")
        access_token = result.get("access_token")

        # Fetch user profile from Microsoft Graph
        profile = get_user_profile(access_token)
        logger.debug(f"User profile: {profile}")
        if not profile:
            return HTMLResponse("Failed to fetch user profile.", status_code=400)

        # Store user info and access token in session
        request.session["user"] = {
            "email": user_email,
            "name": profile.get("displayName", user_name),
            "jobTitle": profile.get("jobTitle", "N/A"),
            "id": profile.get("id"),
            "access_token": access_token
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
    if user.get("jobTitle", "").strip().lower() != "hrmadministrator":
        raise HTTPException(status_code=403, detail="Only HRMAdministrators can access this page.")
    return templates.TemplateResponse("register.html", {"request": request, "error": None})

@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    display_name: str = Form(...),
    email: str = Form(...),
    job_title: str = Form(...),
    password: str = Form(...),
    is_admin: bool = Form(False)
):
    user = request.session.get("user")
    logger.debug(f"Register POST - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if user.get("jobTitle", "").strip().lower() != "hrmadministrator":
        raise HTTPException(status_code=403, detail="Only HRMAdministrators can register users.")
    
    # Create user in Entra ID
    result = create_user(user["access_token"], display_name, email, job_title, password, is_admin)
    if isinstance(result, tuple):
        status_code, error_response = result
        error_message = error_response.get("error", {}).get("message", "Failed to register user in Entra ID.")
        logger.error(f"Registration error: {status_code} - {error_message} - Full response: {error_response}")
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": error_message},
            status_code=400
        )

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/edit_user/{user_id}", response_class=HTMLResponse)
async def edit_user_get(request: Request, user_id: str):
    user = request.session.get("user")
    logger.debug(f"Edit User GET - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if user.get("jobTitle", "").strip().lower() != "hrmadministrator":
        raise HTTPException(status_code=403, detail="Only HRMAdministrators can edit users.")

    # Fetch user details from Microsoft Graph
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
    if user.get("jobTitle", "").strip().lower() != "hrmadministrator":
        raise HTTPException(status_code=403, detail="Only HRMAdministrators can edit users.")
    
    # Update user in Entra ID
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

@app.post("/delete_user/{user_id}", response_class=HTMLResponse)
async def delete_user_post(request: Request, user_id: str):
    user = request.session.get("user")
    logger.debug(f"Delete User POST - Session user: {user}")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)
    if user.get("jobTitle", "").strip().lower() != "hrmadministrator":
        raise HTTPException(status_code=403, detail="Only HRMAdministrators can delete users.")
    
    # Prevent self-deletion
    if user_id == user["id"]:
        return HTMLResponse("Cannot delete your own account.", status_code=400)

    # Delete user in Entra ID
    result = delete_user(user["access_token"], user_id)
    if isinstance(result, tuple):
        status_code, error_response = result
        error_message = error_response.get("error", {}).get("message", "Failed to delete user in Entra ID.")
        logger.error(f"Delete error: {status_code} - {error_message} - Full response: {error_response}")
        return HTMLResponse(f"Failed to delete user: {error_message}", status_code=400)

    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login/microsoft", status_code=303)

    # Fetch all users from Microsoft Graph
    users = get_all_users(user["access_token"])
    if not users:
        return HTMLResponse("Failed to fetch users from Entra ID.", status_code=400)

    # Format users to match the expected employees tuple: (id, name, email, jobTitle)
    employees = [
        (user["id"], user.get("displayName", "N/A"), user.get("userPrincipalName", "N/A"), user.get("jobTitle", "N/A"))
        for user in users
    ]

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": user["email"],
        "employees": employees,
        "user_job_title": user["jobTitle"]
    })

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    tenant = AZURE_AUTHORITY.split('/')[-1]
    post_logout_redirect_uri = "http://localhost:8000/login"
    params = urlencode({"post_logout_redirect_uri": post_logout_redirect_uri})
    azure_logout_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?{params}"
    return RedirectResponse(url=azure_logout_url)