from fastapi import FastAPI
from app.database import Base, engine
from app.routes import auth, admin
import app.models
from app.routes import protected
import logging
import logging.config
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

try:
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Failed to create database tables: {str(e)}")
    raise

# Initialize FastAPI app
app = FastAPI(
    title="Auth System",
    description="Secure authentication system with JWT tokens",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,                   # cookies allow
    allow_methods=["*"],
    allow_headers=["*"],
)
# Include routers
app.include_router(auth.router)
app.include_router(protected.router)
app.include_router(admin.router)

@app.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {"status": "healthy"}

@app.get("/")
def read_root():
    """
    Root endpoint.
    
    Returns:
        Welcome message
    """
    return {"message": "Welcome to Auth System"}

logger.info("Application started successfully")


