from pydantic import BaseModel, field_serializer, Field
from datetime import datetime

class LotCreate(BaseModel):
    title: str
    start_price: float = Field(gt=0)
    duration_seconds: int = Field(gt=0)


class BidCreate(BaseModel):
    bidder: str
    amount: float = Field(gt=0)


class LotOut(BaseModel):
    id: int
    title: str
    current_price: float
    status: str
    end_time: datetime

    @field_serializer("end_time")
    def format_end_time(self, value: datetime):
        return value.strftime("%d %B %Y, %H:%M:%S")

    class Config:
        from_attributes = True
