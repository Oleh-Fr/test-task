import os

from fastapi import FastAPI


app = FastAPI()


@app.get("/")
async def root():
    print(os.getenv("DATABASE_URL"))
    return {"message": "Hello World"}
