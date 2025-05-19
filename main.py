from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from config.db import connect_db
from routes import router
from scripts.listen_gmail import start_gmail_listener_thread
from pipeline.loader_pipeline import start_truck_loader_thread

# Create FastAPI app
app = FastAPI(title="Onusphere API", 
              description="Backend API for Onusphere, including Truck Loading Helper and authentication",
              version="1.0.0")

# Connect to MongoDB database
connect_db()

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    # Change this to match your frontend URL in production
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routes from routes.py
app.include_router(router)

@app.on_event("startup")
def startup_event():
    print("Starting pipeline and Gmail listener...")
    start_truck_loader_thread()
    # start_gmail_listener_thread()
    print("Background services started.")

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn # type: ignore
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
