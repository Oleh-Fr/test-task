import asyncio

from fastapi import FastAPI, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.db import lifespan, get_db
from app.db.models import Lot, Bid
from app.schemas.schemas import LotCreate, BidCreate, LotOut
from app.websocket_manager import manager

app = FastAPI(lifespan=lifespan)


@app.get("/lots", response_model=list[LotOut])
async def get_lots(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lot).where(Lot.status == "running"))
    return result.scalars().all()


@app.post("/lots")
async def create_lot(lot: LotCreate, db: AsyncSession = Depends(get_db)):
    end_time = datetime.now() + timedelta(seconds=lot.duration_seconds)

    new_lot = Lot(
        title=lot.title,
        start_price=lot.start_price,
        current_price=lot.start_price,
        end_time=end_time,
    )

    db.add(new_lot)
    await db.commit()
    await db.refresh(new_lot)

    return new_lot


@app.post("/lots/{lot_id}/bids")
async def place_bid(lot_id: int, bid: BidCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lot).where(Lot.id == lot_id).with_for_update())

    lot = result.scalar_one_or_none()

    if not lot:
        raise HTTPException(status_code=404, detail="Lot not found")

    if lot.status == "ended":
        raise HTTPException(status_code=400, detail="Auction ended")

    if bid.amount <= lot.current_price:
        raise HTTPException(status_code=400, detail="Bid too low")

    # Update price
    lot.current_price = bid.amount

    new_bid = Bid(
        lot_id=lot_id,
        bidder=bid.bidder,
        amount=bid.amount
    )

    db.add(new_bid)
    await db.commit()
    
    if (lot.end_time - datetime.now()).total_seconds() < 30:
        lot.end_time += timedelta(seconds=30)
        await manager.broadcast(lot_id, {
            "type": "time_extended",
            "lot_id": lot_id,
            "new_end_time": lot.end_time.strftime("%d %B %Y, %H:%M:%S")
        })

    await manager.broadcast(lot_id, {
        "type": "bid_placed",
        "lot_id": lot_id,
        "bidder": bid.bidder,
        "amount": bid.amount
    })

    return {"message": "Bid placed"}


@app.websocket("/ws/lots/{lot_id}")
async def websocket_endpoint(websocket: WebSocket, lot_id: int):
    await manager.connect(lot_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(lot_id, websocket)
