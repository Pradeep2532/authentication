from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from app.database import get_db
from app.models.user import User
from app.schemas.auth import SignupSchema, LoginSchema
from app.core.security import hash_password, verify_password, hash_token
from app.core.jwt import create_access_token, create_refresh_token
import os
from app.models.refresh_token import RefreshToken
from datetime import datetime, timedelta
from jose import jwt, JWTError
import logging
from app.models.token import RevokedToken
from app.deps import get_current_user, get_token_payload
import uuid


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/signup")
def signup(data: SignupSchema, db: Session = Depends(get_db)):
    """Create a new user account"""
    try:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Hash password
        try:
            hashed_password = hash_password(data.password)
        except Exception as e:
            logger.error(f"Password hashing failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process password"
            )

        # Create user
        user = User(
            email=data.email,
            hashed_password=hashed_password
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        logger.info(f"User created successfully: {data.email}")
        return {
            "message": "User created successfully",
            "user_id": str(user.id)
        }
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already exists"
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/login")
def login(
    data: LoginSchema,
    response: Response,
    db: Session = Depends(get_db)
):
    """Authenticate user and return tokens"""
    try:
        # Validate environment variables
        access_token_expire = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
        refresh_token_expire = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
        
        if not access_token_expire or not refresh_token_expire:
            logger.error("Missing token expiration environment variables")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuration error"
            )

        # Find user
        try:
            user = db.query(User).filter(User.email == data.email).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error during login: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred"
            )

        # Verify credentials
        if not user:
            logger.warning(f"Login attempt for non-existent user: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        try:
            password_valid = verify_password(data.password, user.hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication error"
            )

        if not password_valid:
            logger.warning(f"Invalid password for user: {data.email}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )

        # Generate tokens
        try:
            access_token = create_access_token(
                {"sub": str(user.id)},
                int(access_token_expire)
            )
            refresh_token = create_refresh_token(
                {"sub": str(user.id)},
                int(refresh_token_expire)
            )
        except Exception as e:
            logger.error(f"Token generation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate tokens"
            )

        # Store hashed refresh token
        try:
            db_token = RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=datetime.utcnow() + timedelta(
                    days=int(refresh_token_expire)
                )
            )
            db.add(db_token)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to store refresh token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process login"
            )

        # Set secure cookie
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=False,   # Set to True in production
            samesite="lax",
            max_age=60 * 60 * 24 * 7
        )

        logger.info(f"User logged in successfully: {data.email}")
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )



@router.post("/refresh")
def refresh_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Rotate refresh token and issue new access token
    """

    # 1️⃣ Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing"
        )

    # 2️⃣ Load env vars
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")
    ACCESS_EXPIRE = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    REFRESH_EXPIRE = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    if not SECRET_KEY or not ALGORITHM:
        raise HTTPException(
            status_code=500,
            detail="JWT configuration error"
        )

    # 3️⃣ Decode refresh token
    try:
        payload = jwt.decode(
            refresh_token_value,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise HTTPException(status_code=401, detail="Invalid token payload")

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # 4️⃣ Check JWT blacklist (logout protection)
    if db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked"
        )

    # 5️⃣ Check refresh token in DB
    token_hash = hash_token(refresh_token_value)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash,
        RefreshToken.is_revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalid or revoked"
        )

    # 6️⃣ Revoke old refresh token
    db_token.is_revoked = True
    db.add(RevokedToken(jti=jti))
    db.commit()

    # 7️⃣ Generate new tokens
    new_access_payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_EXPIRE),
    }

    new_refresh_payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "exp": datetime.utcnow() + timedelta(days=REFRESH_EXPIRE),
    }

    new_access_token = jwt.encode(
        new_access_payload, SECRET_KEY, algorithm=ALGORITHM
    )

    new_refresh_token = jwt.encode(
        new_refresh_payload, SECRET_KEY, algorithm=ALGORITHM
    )

    # 8️⃣ Store new refresh token
    db.add(
        RefreshToken(
            user_id=user_id,
            token_hash=hash_token(new_refresh_token),
            expires_at=datetime.utcnow() + timedelta(days=REFRESH_EXPIRE)
        )
    )
    db.commit()

    # 9️⃣ Update cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,   # 🔥 True in production (HTTPS)
        max_age=60 * 60 * 24 * REFRESH_EXPIRE
    )

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Logout user by revoking refresh token and blacklisting JWT jti
    """

    # 1️⃣ Get refresh token from cookie
    refresh_token_value = request.cookies.get("refresh_token")

    # Even if token missing → logout should succeed (idempotent)
    if not refresh_token_value:
        response.delete_cookie("refresh_token")
        return {"message": "Logged out"}

    # 2️⃣ Load env vars
    SECRET_KEY = os.getenv("SECRET_KEY")
    ALGORITHM = os.getenv("ALGORITHM")

    if not SECRET_KEY or not ALGORITHM:
        raise HTTPException(
            status_code=500,
            detail="JWT configuration error"
        )

    # 3️⃣ Decode refresh token (best-effort)
    jti = None
    try:
        payload = jwt.decode(
            refresh_token_value,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        jti = payload.get("jti")
    except JWTError:
        # token already invalid / expired → still logout
        logger.info("Logout with invalid or expired refresh token")

    # 4️⃣ Blacklist JWT jti (if exists)
    if jti:
        exists = db.query(RevokedToken).filter(
            RevokedToken.jti == jti
        ).first()

        if not exists:
            db.add(RevokedToken(jti=jti))
            db.commit()

    # 5️⃣ Revoke refresh token in DB (best-effort)
    try:
        token_hash = hash_token(refresh_token_value)

        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False
        ).first()

        if db_token:
            db_token.is_revoked = True
            db.commit()

    except Exception as e:
        logger.error(f"Failed to revoke refresh token: {str(e)}")

    # 6️⃣ Clear cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax",
        secure=False   # 🔥 True in production (HTTPS)
    )

    return {"message": "Logged out successfully"}