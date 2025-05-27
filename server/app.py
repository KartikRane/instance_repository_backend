import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.app_config import PROBLEMS


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)

# read from environment variable
IRB_ROOT = os.getenv("IRB_ROOT", "/")
app = FastAPI(root_path=IRB_ROOT)
IRB_DOMAIN = os.getenv("IRB_DOMAIN", "")
allowed_origins = [
    "http://localhost",  # Allow requests from localhost
    "http://localhost:8080",  # Allow requests from localhost with port 8080
]
if IRB_DOMAIN:
    allowed_origins.append(IRB_DOMAIN)
# Add CORS middleware to allow public access
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Disable cookies and authentication headers
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

for problem in PROBLEMS:
    problem.build_routes(app)
