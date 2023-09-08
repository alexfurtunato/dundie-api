from fastapi import FastAPI
from dundie.models.user import User, UserResponse
from sqlmodel import Session, select
from dundie.db import ActiveSession

app = FastAPI(
    title="Dundie",
    version="0.1.0",
    description="Dundie ie a rewards API", 
)
