# database/schemas.py

from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class AllocationCreate(BaseModel):
    employee_id: str
    vehicle_id: str
    allocation_date: date

class AllocationUpdate(BaseModel):
    vehicle_id: Optional[str]  # Make optional to allow updating only the date
    allocation_date: date

class AllocationResponse(BaseModel):
    id: str
    employee_id: str
    vehicle_id: str
    allocation_date: date

class AllocationHistoryResponse(BaseModel):
    allocations: List[AllocationResponse]
