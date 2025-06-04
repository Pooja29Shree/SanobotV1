from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta

# Password hashing config
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT config
SECRET_KEY = "your-secret-key-utils"  # Different key to avoid conflicts
ALGORITHM = "HS256"

# --------------------------
# 🔐 Password-related utils
# --------------------------

def hash_password_util(password: str) -> str:
    """Hash a password using bcrypt (utility version)"""
    return pwd_context.hash(password)

def verify_password_util(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (utility version)"""
    return pwd_context.verify(plain_password, hashed_password)

# --------------------------
# 🔐 Token-related utils
# --------------------------

def create_access_token_util(data: dict, expires_delta: timedelta = None) -> str:
    """Creates a JWT token with optional custom expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token_util(token: str) -> dict:
    """Verifies and decodes JWT token (utility version)"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def create_refresh_token_util(data: dict) -> str:
    """Create a JWT refresh token with longer expiration (utility version)"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)