Fonteyn Holiday Parks – Cloud Migration

A student project (Fontys, team Cloud Mesh) that moves the IT of a fictional multi-park holiday company, Fonteyn Holiday Parks, from separate on-site setups to one centralized Azure environment.

Status: archived. Built in 2025 as a school project and not maintained since.

1. What is this project?

Fonteyn runs holiday parks in several countries (for example Germany and Belgium). Each park had its own IT, its own booking software and its own barrier hardware, which made everything expensive to run and hard to integrate. The assignment was to centralize that in the cloud and cover four needs:

Need	What we built
Booking	A guest-facing web app to browse accommodations (villa, cottage and others), register, log in and make reservations. Admins get a dashboard to create, update and delete reservations.
Staff / HR access management	An HRM portal where staff sign in with Microsoft and admins manage users and group memberships in Entra ID. Access follows job title and team role.
Energy monitoring	A dashboard with live and 30-day energy consumption, so the environmental team can track CO₂ impact. The readings are simulated, not from real sensors.
Access barrier	A Raspberry Pi with a camera that reads license plates (OpenALPR) and checks them against reservations. It keeps a local SQLite copy of the reservations so the barrier still works during an internet outage.
Architecture
                      Microsoft Entra ID tenant
          (users, groups, app registrations, SSO for both apps)
                                  │
 Internet ── HTTPS ──►  Azure Virtual Network
                       ┌─────────────────────────────────────────┐
                       │  Web tier (Docker containers)           │
                       │   /booking  → Booking app (Flask)       │
                       │   /hrm      → HRM portal (FastAPI)      │
                       │                 │                       │
                       │  Data tier      ▼                       │
                       │   Azure Database for MySQL              │
                       └─────────────────────────────────────────┘
                                      ▲
     Raspberry Pi at the park gate ───┘  (syncs reservations, reads plates)

The Azure environment was built by hand in the Azure portal, without Terraform or any other infrastructure-as-code. It consists of an Entra ID organisation and a virtual network that holds the web server and the database. Only the application code and the container and Kubernetes manifests are in this repository.

The Azure team worked with separate Core, Dev and Prod environments and a <env>-<service>-<type> naming convention (for example dev-app-storage). See documents/Fonteyn_Azure_Manual_Team_Guide.pdf.

2. Tech stack

Applications

Component	Technology
Booking app (test2/)	Python 3.13, Flask, Flask-SQLAlchemy, Waitress, Jinja2 templates, bcrypt
HRM portal (HRM/)	Python 3.13, FastAPI, Uvicorn, Starlette sessions, Jinja2 templates
Authentication	Microsoft Entra ID (OAuth 2.0 / OIDC) through MSAL, Microsoft Graph API for user and group management
Database	MySQL (Azure Database for MySQL Flexible Server, SSL enforced)
Gate controller (Raspberry Pi/)	Python, OpenCV, OpenALPR, libcamera, SQLAlchemy and SQLite, schedule
Integrations	ERPNext (REST API) for accounting and ERP data

Cloud and DevOps

Area	Technology
Cloud	Microsoft Azure, created manually in the portal (no IaC)
Identity	Microsoft Entra ID organisation
Network	Azure virtual network with a web server tier and a database tier
Containers	Docker and Docker Compose, images in Azure Container Registry (fonteyncr.azurecr.io)
Orchestration	Kubernetes manifests (Deployment, Service, Ingress) with NGINX ingress and TLS
CI/CD	GitLab CI (.gitlab-ci.yml): build and push images, then deploy
3. How to deploy
Prerequisites (Azure, created manually)
A Microsoft Entra ID tenant with two app registrations, one for Booking and one for HRM. Each needs a redirect URI and a client secret.
Booking redirect: https://<host>/booking/admin/msauth
HRM redirect: the AZURE_REDIRECT_URI value, ending in /hrm/auth/callback
HRM needs these Microsoft Graph permissions, with admin consent: User.Read, User.Read.All, User.ReadWrite.All, GroupMember.Read.All, Group.Read.All, Directory.ReadWrite.All
Create an Entra group for HRM admins and note its object ID (HRM_ADMIN_GROUP_ID).
A virtual network with a web tier (the hosts or nodes running the containers) and a database tier.
An Azure Database for MySQL Flexible Server reachable from the web tier, with an empty database. The Booking app creates its tables and a default admin account on first start.
An Azure Container Registry. The manifests expect fonteyncr.azurecr.io, so change the name in docker-compose.yml and in the k8s/deployment.yml files if you use another.
For the Kubernetes route, an AKS cluster with the NGINX ingress controller installed. The pods use nodeSelector labels, so label one node app=booking and one app=hrm.
Configuration

Both apps read a .env file. Never commit it.

Booking (test2/.env)

env
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=
ERP_API_KEY=
ERP_API_SECRET=
CLIENT_ID=                 # Entra app registration
CLIENT_SECRET=
ENTRA_ID_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
REDIRECT_URI=https://<host>/booking/admin/msauth
ENTRA_ID_SCOPE=User.Read

HRM (HRM/.env)

env
SECRET_KEY=
API_KEY=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_AUTHORITY=https://login.microsoftonline.com/<tenant-id>
AZURE_REDIRECT_URI=https://<host>/hrm/auth/callback
HRM_ADMIN_GROUP_ID=

HRM/.env_example uses older variable names. Use the names above, which are what HRM/environment.py reads.

Raspberry Pi (Raspberry Pi/.env): DB_HOST, DB_USER, DB_PASSWORD, DB_NAME.

Option A: run locally
bash
# Booking app  ->  http://localhost:5000/booking
cd test2
pip install -r requirements.txt
python app.py

# HRM portal   ->  http://localhost:8000/hrm
cd HRM
pip install -r requirements.txt
uvicorn main:main_app --host 0.0.0.0 --port 8000

Or build both images with Docker Compose. This needs HRM/.env to exist, and the Booking app needs a .env in test2/ (it is copied into the image at build time):

bash
docker-compose up --build -d
Option B: deploy to Azure with GitLab CI

Push to the default branch and the pipeline in .gitlab-ci.yml does the following:

build: runs docker-compose up --build, tags both images with the short commit SHA and pushes them to Azure Container Registry.
deploy (deploy_booking, deploy_hrm): logs in to Azure with a service principal, fetches AKS credentials, creates the TLS secrets and the .env ConfigMaps, then applies the Ingress, Deployment (with the image tag filled in) and Service manifests.

Set these CI/CD variables in GitLab first:

Variable	Purpose
REGISTRY_USER, REGISTRY_PASSWORD	Azure Container Registry login
AZ_CLIENT_ID, AZ_CLIENT_SECRET, AZ_TENANT_ID	Service principal used by the pipeline
AKS_RG, AKS_CLUSTER	Resource group and name of the AKS cluster
HRM_TLS_CRT, HRM_TLS_KEY	TLS certificate and key for the HRM ingress
BOOKING_TLS_CRT, BOOKING_TLS_KEY	TLS certificate and key for the Booking ingress
HRM_ENV_FILE, BOOKING_ENV_FILE	Full contents of each app's .env

After deployment the apps are served behind the ingress at /booking and /hrm. The Booking app also exposes /health.

Raspberry Pi gate controller

On a Pi with a camera module:

bash
sudo apt install libcamera-apps openalpr openalpr-utils
cd "Raspberry Pi"
pip install -r requirements.txt
python main.py

It syncs reservations from MySQL into the local license-plate.db every 10 seconds, captures frames and logs whether each detected plate is expected to check in.

4. Repository layout
.
├── .gitlab-ci.yml          # CI/CD: build images -> push to ACR -> deploy to AKS
├── docker-compose.yml      # Builds the booking and hrm images
├── test2/                  # Booking app (Flask): the deployed guest-facing app
│   ├── app.py              #   routes, admin dashboard, energy API, /health
│   ├── entra_auth.py       #   Entra ID (MSAL) login
│   ├── models.py           #   User, Reservation, EnergyUsageDaily
│   ├── energy.py           #   simulated energy-usage monitor
│   ├── accommodations.yaml #   accommodation types and prices
│   ├── templates/, static/ #   Jinja2 pages and CSS
│   ├── k8s/                #   Deployment, Service, Ingress
│   └── README_ENTRA_ID.md  #   Entra ID setup notes for the booking app
├── HRM/                    # HR / identity portal (FastAPI)
│   ├── main.py             #   routes: login, dashboard, user create/edit/delete
│   ├── azure.py            #   Microsoft Graph helpers (users, groups)
│   ├── environment.py      #   env var loading
│   ├── templates/, static/
│   └── k8s/                #   Deployment, Service, Ingress
├── Raspberry Pi/           # Gate controller: license-plate recognition + local DB
├── backend/                # Early FastAPI + JWT API prototype (not deployed)
├── reservation_system/     # Early domain-model prototype (not deployed)
└── documents/              # Project plan, design document, sprint backlogs and
                            # reviews, GDPR, business continuity and capacity
                            # plans, user guide, Azure team guide

The folder test2/ is the production Booking app. It kept its original working name.

Documentation

Planning, design and compliance material lives in documents/. Start with Project_Plan_-_Cloud_Mesh_v2.docx and Design_Document_Cloud_Mesh_draft1.docx.

Authors

Team Cloud Mesh, Fontys University of Applied Sciences.
