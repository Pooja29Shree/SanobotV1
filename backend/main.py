# main.py
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from .database import Base, engine, SessionLocal
from . import models, schemas
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from .auth import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token
)
from jose import JWTError
from typing import Optional
Base.metadata.create_all(bind=engine)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
except Exception as e:
    print(f"Error creating database tables: {e}")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
app = FastAPI(title="ChatBot API", version="1.0.0")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Verify user exists in database
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/signup", response_model=schemas.MessageResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if user already exists
        db_user = db.query(models.User).filter(models.User.email == user.email).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        hashed = hash_password(user.password)
        new_user = models.User(email=user.email, hashed_password=hashed)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return {"msg": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/token", response_model=schemas.TokenResponse)
def login_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {"sub": user.email}
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token(payload)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/login", response_model=schemas.TokenResponse)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    payload = {"sub": user.email}
    return {
        "access_token": create_access_token(payload),
        "refresh_token": create_refresh_token(payload),
        "token_type": "bearer"
    }

@app.post("/refresh", response_model=dict)
def refresh_token(refresh_token: str = Header(..., alias="refresh-token")):
    try:
        data = decode_token(refresh_token)
        new_access_token = create_access_token({"sub": data["sub"]})
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@app.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.post("/logout", response_model=schemas.MessageResponse)
def logout():
    # Stateless logout - frontend should remove tokens
    return {"msg": "Logged out successfully. Please remove tokens from client."}

@app.post("/chat", response_model=schemas.MessageResponse)
def save_chat(
    msg: schemas.ChatMessage, 
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Save chat message
    db_msg = models.ChatHistory(
        user_id=current_user.id, 
        role=msg.role, 
        message=msg.message
    )
    db.add(db_msg)
    db.commit()
    
    return {"msg": "Chat message saved successfully"}

@app.get("/chat", response_model=schemas.ChatHistoryResponse)
def get_chat(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100, description="Number of messages to retrieve"),
    offset: int = Query(0, ge=0, description="Number of messages to skip")
):
    # Get total count
    total_count = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).count()
    
    # Get messages with pagination, ordered by creation time (newest first)
    messages = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == current_user.id)
        .order_by(models.ChatHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    
    return {
        "messages": messages,
        "total_count": total_count
    }

@app.get("/chat/recent", response_model=list[schemas.ChatMessageResponse])
def get_recent_chat(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(10, ge=1, le=50, description="Number of recent messages")
):
    """Get recent chat messages for quick access"""
    messages = (
        db.query(models.ChatHistory)
        .filter(models.ChatHistory.user_id == current_user.id)
        .order_by(models.ChatHistory.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return messages

@app.delete("/chat", response_model=schemas.MessageResponse)
def clear_chat_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all chat history for the current user"""
    # Delete all chat messages for this user
    deleted_count = db.query(models.ChatHistory).filter(models.ChatHistory.user_id == current_user.id).delete()
    db.commit()
    
    return {"msg": f"Cleared {deleted_count} chat messages"}

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "ChatBot API is running"}

# Debug endpoint to check database
@app.get("/debug/tables")
def debug_tables():
    return {"tables": list(Base.metadata.tables.keys())}