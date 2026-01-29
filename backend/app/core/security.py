from passlib.context import CryptContext
import hashlib
import logging

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password to hash
        
    Returns:
        Hashed password
        
    Raises:
        ValueError: If password hashing fails
    """
    try:
        if not password or len(password) == 0:
            raise ValueError("Password cannot be empty")
        
        if len(password) > 72:
            raise ValueError("Password is too long (max 72 characters)")
            
        hashed = pwd_context.hash(password)
        return hashed
    except ValueError as e:
        logger.error(f"Password validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during password hashing: {str(e)}")
        raise ValueError("Failed to hash password")

def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        hashed: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
        
    Raises:
        ValueError: If verification fails
    """
    try:
        if not password or not hashed:
            logger.warning("Password or hash is empty")
            return False
            
        result = pwd_context.verify(password, hashed)
        return result
    except Exception as e:
        logger.error(f"Error during password verification: {str(e)}")
        raise ValueError("Failed to verify password")

def hash_token(token: str) -> str:
    """
    Hash a token using SHA256.
    
    Args:
        token: Token to hash
        
    Returns:
        Hashed token
        
    Raises:
        ValueError: If token hashing fails
    """
    try:
        if not token or len(token) == 0:
            raise ValueError("Token cannot be empty")
            
        hashed = hashlib.sha256(token.encode()).hexdigest()
        return hashed
    except ValueError as e:
        logger.error(f"Token validation error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error during token hashing: {str(e)}")
        raise ValueError("Failed to hash token")