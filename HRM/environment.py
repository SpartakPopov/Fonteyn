import os

from dotenv import find_dotenv, load_dotenv
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

dotenv_path = find_dotenv()

load_dotenv(dotenv_path)

SECRET_KEY = os.getenv("SECRET_KEY")
API_KEY = os.getenv("API_KEY")