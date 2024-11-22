from fastapi import FastAPI
from typing import Dict
import os

app = FastAPI()

@app.get("/")
async def root() -> Dict[str, str]:
    return {"message": "Welcome to KamiBlue Backend!"}
