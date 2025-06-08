from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from urllib.parse import urlencode
from starlette.middleware.sessions import SessionMiddleware
from db import get_password, register_employee, all_employees, edit_employee, delete_employee, get_pending_users,approve_pending_user, reject_pending_user
from passlib.hash import bcrypt
from msal import ConfidentialClientApplication
from environment import AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_AUTHORITY, AZURE_REDIRECT_URI, AZURE_SCOPE, SECRET_KEY
    
templates = Jinja2Templates(directory="templates")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
# mounting the static folder
app.mount("/static", StaticFiles(directory="static"), name="static")


def _build_msal_app():
    return ConfidentialClientApplication(
        AZURE_CLIENT_ID,    
        authority=AZURE_AUTHORITY,
        client_credential=AZURE_CLIENT_SECRET
    )

# routes
@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse(url="/login")


@app.get("/register", response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
async def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login/microsoft")
async def login_microsoft():
    msal_app = _build_msal_app()
    auth_url = msal_app.get_authorization_request_url(
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return HTMLResponse("Login failed: No code provided.", status_code=400)

    msal_app = _build_msal_app()
    result = msal_app.acquire_token_by_authorization_code(
        code,
        scopes=AZURE_SCOPE,
        redirect_uri=AZURE_REDIRECT_URI
    )

    if "access_token" in result:
        user_email = result.get("id_token_claims", {}).get("preferred_username") or result.get("account", {}).get("username")
        user_name = result.get("id_token_claims", {}).get("name", "Microsoft User")

        # Store email in session
        request.session["username"] = user_email
        return RedirectResponse(url="/dashboard", status_code=303)

    return HTMLResponse(f"Login failed: {result.get('error_description')}", status_code=400)



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    username = request.session.get("username")
    print("Dashboard accessed by user:", username)
    if not username:
        print("Not in session, redirecting to login")
        return RedirectResponse(url="/login", status_code=303)

    employees = all_employees()
    pending_emps = []

    if username == "admin":
        pending_emps = get_pending_users()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "username": username,
        "employees": employees,
        "pending_employees": pending_emps
    })



@app.get("/pending_users", response_class=HTMLResponse)
async def pending_users(request: Request):
    username = request.session.get("username")
    if username != "admin":
        return RedirectResponse(url="/login", status_code=303)

    pending_emps = get_pending_users()

    return templates.TemplateResponse("pending_users.html", {
        "request": request,
        "employees": pending_emps
    })


@app.post("/register", response_class=HTMLResponse)
async def register_post(
    request: Request,
    username: str = Form(...),
    names: str = Form(...),
    email: str = Form(...),
    position: str = Form(...),
    password: str = Form(...)
):
    form = await request.form()
    print("Form data received:", form)
    success = register_employee(username, names, email, position, password)
    if not success:
        error = "Username already exists."
        return templates.TemplateResponse("register.html", {"request": request, "error": error})

    return RedirectResponse(url="/login", status_code=303)


@app.post("/login", response_class=HTMLResponse)
async def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    stored_password = get_password(username)

    if stored_password is None:
        error = "Username not found."
    elif not bcrypt.verify(password, stored_password): 
        error = "Incorrect password."
    else:
        request.session["username"] = username
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    tenant = AZURE_AUTHORITY.split('/')[-1] 
    post_logout_redirect_uri = "http://localhost:8000/login"  

    params = urlencode({"post_logout_redirect_uri": post_logout_redirect_uri})
    azure_logout_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/logout?{params}"
    return RedirectResponse(url=azure_logout_url)


@app.post("/edit_employee/{username}")
async def edit_employee_api(username: str, request: Request):
    data = await request.json()
    names = data.get("names")
    email = data.get("email")
    position = data.get("position")

    try:
        edit_employee(username, names, email, position)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)


@app.delete("/delete_employee/{username}")
async def delete_employee_api(username: str):
    try:
        delete_employee(username)
        return JSONResponse(content={"status": "success"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)





@app.post("/approve_user/{username_to_approve}")
async def approve_user(request: Request, username_to_approve: str):
    if request.session.get("username") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        approve_pending_user(username_to_approve)
        return JSONResponse(content={"status": "success", "message": f"Employee {username_to_approve} approved"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)


@app.post("/reject_user/{username_to_reject}")
async def reject_pending_user_api(request: Request, username_to_reject: str):
    if request.session.get("username") != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        reject_pending_user(username_to_reject)
        return JSONResponse(content={"status": "success", "message": f"Employee {username_to_reject} rejected"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "detail": str(e)}, status_code=500)