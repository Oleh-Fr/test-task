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
        raise HTTPException(404, "Lot not found")

    if lot.status != "running":
        raise HTTPException(400, "Auction is not running")

    if lot.end_time <= datetime.now():
        raise HTTPException(400, "Auction ended")

    if bid.amount <= lot.current_price:
        raise HTTPException(400, "Bid too low")

    # Update lot and add bid in same transaction
    lot.current_price = bid.amount
    new_bid = Bid(lot_id=lot_id, bidder=bid.bidder, amount=bid.amount)
    db.add(new_bid)

    if (lot.end_time - datetime.now()).total_seconds() < 30:
        lot.end_time += timedelta(seconds=30)

    await db.commit()
    await db.refresh(lot)

    # Broadcast updates
    try:
        await manager.broadcast(lot_id, {
            "type": "bid_placed",
            "lot_id": lot_id,
            "bidder": bid.bidder,
            "amount": bid.amount,
            "new_end_time": lot.end_time.isoformat()
        })
    except Exception:
        pass  # Avoid crashing if a client disconnects

    return {"message": "Bid placed", "current_price": lot.current_price, "end_time": lot.end_time.isoformat()}


@app.websocket("/ws/lots/{lot_id}")
async def websocket_endpoint(websocket: WebSocket, lot_id: int):
    await manager.connect(lot_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(lot_id, websocket)
