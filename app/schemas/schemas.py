from enum import Enum

from pydantic import BaseModel


class Status(str, Enum):
    running = "running"
    ended = "ended"


class CreateLot(BaseModel):
    price: float
