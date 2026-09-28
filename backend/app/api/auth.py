from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False
)
async def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user account.
    - Validates email format.
    - Prevents duplicate accounts.
    - Hashes password securely with bcrypt before storing.
    - Issues a JWT access token for immediate session initiation.
    """
    # Check for duplicate email
    existing_user = db.query(User).filter(User.email.ilike(user_in.email.strip())).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists."
        )

    # Securely hash password
    hashed_pwd = hash_password(user_in.password)

    # Create user record
    new_user = User(
        email=user_in.email.strip().lower(),
        full_name=user_in.full_name.strip(),
        hashed_password=hashed_pwd,
        role=user_in.role or UserRole.ANALYST,
        operator_team_id=user_in.operator_team_id,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Issue JWT access token
    role_str = new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role)
    token = create_access_token(subject=new_user.id, role=role_str)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user)
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and return JWT access token"
)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates a user with email and password.
    - Validates credentials against stored bcrypt hash.
    - Checks account active status.
    - Returns signed JWT token on success.
    """
    user = db.query(User).filter(User.email.ilike(credentials.email.strip())).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been disabled."
        )

    role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    token = create_access_token(subject=user.id, role=role_str)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current authenticated user profile"
)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the profile of the currently authenticated user.
    - Requires valid Bearer JWT in Authorization header.
    - Does not expose hashed password.
    """
    return UserResponse.model_validate(current_user)
