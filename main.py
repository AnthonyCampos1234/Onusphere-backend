from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.routes import router
from config.db import connect_db

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

# Run with: uvicorn main:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
