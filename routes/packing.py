from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import os
from scripts.truck_loader.simulation.packing_engine import PackingEngine

router = APIRouter()

# Persistent simulation engine
engine = None

def get_engine():
    global engine
    if engine is None:
        engine = PackingEngine()

        sim_states_dir = os.path.join(os.path.dirname(__file__),"..", "..", "backend", "scripts", "truck_loader", "sim_states")
        file_path = os.path.abspath(os.path.join(sim_states_dir, "sim2_g1.json"))

        print("Resolved sim_states_dir:", sim_states_dir)
        print("Loading initial state from:", file_path)

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"❌ sim2_g1.json not found at: {file_path}")

        engine.load_state(file_path)

    return engine

# Request models
class LoadStateRequest(BaseModel):
    filename: str

class PlaceItemRequest(BaseModel):
    item_id: int
    truck_id: int
    position: List[float]
    rotation: List[float]

# Routes
@router.get("/status")
def status():
    return {
        "status": "operational",
        "version": "0.1.0"
    }

@router.post("/load_state")
def load_state(payload: LoadStateRequest):
    engine = get_engine()
    engine.load_state(payload.filename)
    return {"status": "success"}

@router.get("/simulations/{filename}")
def get_simulation(filename: str):
    engine = get_engine()
    return engine.get_state()

@router.post("/place_item")
def place_item(payload: PlaceItemRequest):
    engine = get_engine()
    if not all([payload.item_id, payload.truck_id, payload.position, payload.rotation]):
        raise HTTPException(status_code=400, detail="Missing required parameters.")
    
    result = engine.place_item(
        payload.item_id,
        payload.truck_id,
        payload.position,
        payload.rotation
    )

    if result:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=400, detail="Failed to place item. Invalid placement.")

@router.get("/get_state")
def get_state():
    engine = get_engine()
    return engine.get_state()

