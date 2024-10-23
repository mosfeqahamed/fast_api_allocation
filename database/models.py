# database/models.py

from datetime import date
from pydantic import BaseModel, Field
from bson import ObjectId
from config import db
from motor.motor_asyncio import AsyncIOMotorClient

class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    name: str

class Vehicle(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    license_plate: str
    driver_id: str

class Allocation(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()), alias="_id")
    employee_id: str
    vehicle_id: str
    allocation_date: date
