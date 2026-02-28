import os

from fastapi import FastAPI


from schemas.schemas import CreateLot


app = FastAPI()


@app.get("/lots")
async def get_lots():
    ...


@app.post("/lots")
async def create_lot(lot: CreateLot):
    ...


@app.post("/lots/{lot_id}/bids")
async def create_lot_bids():
    ...
