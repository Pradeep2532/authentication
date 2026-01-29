from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, status
import os
import logging
import uuid
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")


# Internal helpers
def _validate_secrets() -> Tuple[str, str]:
    if not SECRET_KEY:
        logger.error("SECRET_KEY environment variable is not set")
        raise ValueError("SECRET_KEY is required")

    if not ALGORITHM:
        logger.error("ALGORITHM environment variable is not set")
        raise ValueError("ALGORITHM is required")

    return SECRET_KEY, ALGORITHM


def _base_encode(data: dict, expires_delta: timedelta) -> str:
    secret_key, algorithm = _validate_secrets()

    to_encode = data.copy()
    to_encode.update({
        "exp": datetime.utcnow() + expires_delta,
        "jti": str(uuid.uuid4()),  # 🔥 CRITICAL
    })

    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


# Token creation
def create_access_token(data: dict, expires_minutes: int) -> str:
    if expires_minutes <= 0:
        raise ValueError("Expiration time must be positive")

    try:
        return _base_encode(
            data=data,
            expires_delta=timedelta(minutes=expires_minutes),
        )
    except Exception as e:
        logger.error(f"Failed to create access token: {str(e)}")
        raise ValueError("Failed to create access token")


def create_refresh_token(data: dict, expires_days: int) -> str:
    if expires_days <= 0:
        raise ValueError("Expiration time must be positive")

    try:
        return _base_encode(
            data=data,
            expires_delta=timedelta(days=expires_days),
        )
    except Exception as e:
        logger.error(f"Failed to create refresh token: {str(e)}")
        raise ValueError("Failed to create refresh token")


# Token decode (shared)
def decode_token(token: str) -> Dict[str, str]:
    """
    Decode JWT and return payload (sub, jti).
    Used by access & refresh flows.
    """
    try:
        secret_key, algorithm = _validate_secrets()

        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing",
            )

        payload = jwt.decode(token, secret_key, algorithms=[algorithm])

        sub = payload.get("sub")
        jti = payload.get("jti")

        if not sub or not jti:
            logger.warning("Token missing required claims")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        return {
            "sub": sub,
            "jti": jti,
        }

    except HTTPException:
        raise
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication configuration error",
        )
    except Exception as e:
        logger.error(f"Unexpected error during token decode: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token validation error",
        )


# Access-token specific helper
def decode_access_token(token: str) -> str:
    """
    Decode access token and return user_id only.
    """
    payload = decode_token(token)
    return payload["sub"]
