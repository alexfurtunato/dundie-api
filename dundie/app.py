from fastapi import FastAPI
from dundie.routes import main_router


app = FastAPI(
    title="Dundie",
    version="0.1.0",
    description="Dundie ie a rewards API", 
)

app.include_router(main_router)
