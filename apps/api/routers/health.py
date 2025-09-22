from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "SecretHawk API"
    }

@router.post("/auth/login")
async def login(credentials: dict):
    """Simple authentication endpoint for MVP"""
    from core.security import authenticate_user, create_access_token
    
    username = credentials.get("username")
    password = credentials.get("password")
    
    if not username or not password:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )
    
    user = authenticate_user(username, password)
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    access_token = create_access_token({"sub": username, "role": user["role"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 3600
    }