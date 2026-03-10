from pydantic import BaseModel, Field
from typing import List, Optional


class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    role: str = "customer"
    phone: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class BikeCreate(BaseModel):
    name: str
    type: str
    brand: str
    model: str
    year: int = 2024
    engine_cc: int
    daily_rate: float
    weekly_rate: Optional[float] = None
    images: List[str] = []
    features: List[str] = []
    location: str = "Leh"
    description: str = ""


class ShopCreate(BaseModel):
    name: str
    description: str = ""
    address: str = ""
    phone: str = ""
    operating_hours_open: str = "08:00"
    operating_hours_close: str = "20:00"


class BookingCreate(BaseModel):
    bike_id: str
    start_date: str
    end_date: str
    notes: str = ""


class ReviewCreate(BaseModel):
    booking_id: str
    rating: int
    comment: str = ""


class PaymentProcess(BaseModel):
    booking_id: str
    amount: float
    payment_method: str = "mock_gateway"
