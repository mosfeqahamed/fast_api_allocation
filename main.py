# main.py
from fastapi import FastAPI, HTTPException
from datetime import datetime
from database.models import Allocation
from database.schemas import AllocationCreate, AllocationUpdate, AllocationResponse, AllocationHistoryResponse
from bson import ObjectId
from config import db
from config import client  # Import MongoDB client from config.py
from pymongo.errors import ConnectionFailure
from typing import List
from fastapi import Query
from motor.motor_asyncio import AsyncIOMotorClient

app = FastAPI()


@app.get("/healthcheck")
async def healthcheck():
    try:
       
        await client.server_info()  
        return {"status": "MongoDB connection successful"}
    except ConnectionFailure:
        return {"status": "MongoDB connection failed"}, 500

@app.post("/allocations/", response_model=AllocationResponse)
async def create_allocation(allocation: AllocationCreate):
    # Convert allocation_date to datetime
    allocation_datetime = datetime.combine(allocation.allocation_date, datetime.min.time())
    
    # Check if the vehicle is already allocated on the specified date
    existing_allocation = await db["allocations"].find_one({
        "vehicle_id": allocation.vehicle_id,
        "allocation_date": allocation_datetime
    })
    
    if existing_allocation:
        raise HTTPException(status_code=400, detail="Vehicle already allocated for this date.")

    # Prepare the allocation data to be inserted
    allocation_dict = allocation.dict(exclude_unset=True)
    allocation_dict["_id"] = str(ObjectId())  # MongoDB uses _id for the primary key
    allocation_dict["allocation_date"] = allocation_datetime  # Store as datetime object

    # Insert into MongoDB
    await db["allocations"].insert_one(allocation_dict)

    # Convert the inserted data to AllocationResponse, replacing _id with id
    allocation_dict["id"] = allocation_dict["_id"]  # Replace _id with id for the response
    allocation_dict["allocation_date"] = allocation_datetime.date()  # Convert back to date

    return AllocationResponse(**allocation_dict)

@app.get("/allocations/", response_model=List[AllocationResponse])
async def get_allocations():
    allocations = await db["allocations"].find().to_list(length=None)  # Fetch all allocations
    print(f"Looking for allocation with ID: {allocations})")
    response = []
    
    for allocation in allocations:
        allocation["id"] = str(allocation["_id"])  # Replace _id with id
        allocation["allocation_date"] = allocation["allocation_date"].date()  # Convert back to date
        response.append(AllocationResponse(**allocation))

    return response

@app.get("/allocations/{allocation_id}", response_model=AllocationResponse)
async def get_allocation(allocation_id: str):
    try:
        allocation_object_id = ObjectId(allocation_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid allocation ID.")

    allocation_data = await db["allocations"].find_one({"_id": "allocation_object_id"})
    print(f"Looking for allocation with ID: {allocation_data} (ObjectId: {allocation_object_id})")
    if not allocation_data:
        raise HTTPException(status_code=404, detail="Allocation not found.")

    allocation_data["id"] = str(allocation_data["_id"])
    allocation_data["allocation_date"] = allocation_data["allocation_date"].date()

    return AllocationResponse(**allocation_data)


@app.put("/allocations/{allocation_id}", response_model=AllocationResponse)
async def update_allocation(allocation_id: str, allocation: AllocationUpdate):
    # Validate ObjectId
    try:
        allocation_object_id = ObjectId(allocation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid allocation ID.")
    
    # Check if the allocation exists
    allocation_data = await db["allocations"].find_one({"_id": allocation_object_id})

    if not allocation_data:
        raise HTTPException(status_code=404, detail="Allocation not found.")

    # Prepare the updated data
    updated_data = allocation.dict(exclude_unset=True)  # Exclude unset fields
    if "allocation_date" in updated_data:
        updated_data["allocation_date"] = datetime.combine(allocation.allocation_date, datetime.min.time())  # Convert to datetime

    # Update the allocation in the database if there are updates
    await db["allocations"].update_one({"_id": allocation_object_id}, {"$set": updated_data})

    # Retrieve the updated allocation
    updated_allocation = await db["allocations"].find_one({"_id": allocation_object_id})

    # Convert _id to id for the response
    updated_allocation["id"] = str(updated_allocation["_id"])
    updated_allocation["allocation_date"] = updated_allocation["allocation_date"].date()  # Convert back to date

    return AllocationResponse(**updated_allocation)


@app.delete("/allocations/{allocation_id}", response_model=dict)
async def delete_allocation(allocation_id: str):
    # Validate ObjectId
    try:
        allocation_object_id = ObjectId(allocation_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid allocation ID.")
    
    print(f"Looking for allocation with ID: {allocation_id} (ObjectId: {allocation_object_id})")

    # Check if the allocation exists
    allocation_data = await db["allocations"].find_one({"_id": allocation_object_id})
    
    if allocation_data is None:
        print(f"No allocation found with ID: {allocation_id}")
        raise HTTPException(status_code=404, detail="Allocation not found.")

    # Delete the allocation
    result = await db["allocations"].delete_one({"_id": allocation_object_id})
    
    if result.deleted_count == 0:
        print(f"Failed to delete allocation with ID: {allocation_id}")
        raise HTTPException(status_code=404, detail="Allocation not found.")

    print(f"Allocation with ID: {allocation_id} deleted successfully.")
    return {"detail": "Allocation deleted successfully."}


@app.get("/allocations/history/", response_model=AllocationHistoryResponse)
async def get_allocation_history(employee_id: str = Query(None), vehicle_id: str = Query(None)):
    # Initialize the query object
    query = {}

    # Add employee_id to query if provided
    if employee_id:
        query["employee_id"] = employee_id
    
    # Add vehicle_id to query if provided
    if vehicle_id:
        query["vehicle_id"] = vehicle_id

    # Fetch allocations based on the query
    allocations = []
    async for alloc in db["allocations"].find(query):
        # Convert _id to id for each allocation
        alloc["id"] = str(alloc["_id"])
        # Convert allocation_date from datetime to date
        alloc["allocation_date"] = alloc["allocation_date"].date()
        # Append to response list
        allocations.append(AllocationResponse(**alloc))

    # Return the filtered history of allocations
    return AllocationHistoryResponse(allocations=allocations)

