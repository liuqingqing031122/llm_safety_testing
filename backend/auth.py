from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
import secrets

from backend import schemas, security
from backend.models.database import get_db
from backend.models import User
from backend.email_service import send_reset_email

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.responses import RedirectResponse
import httpx
import os


config = Config(os.path.join(os.path.dirname(__file__), '.env'))
oauth = OAuth(config)

oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

oauth.register(
    name='github',
    client_id=os.getenv('GITHUB_CLIENT_ID'),
    client_secret=os.getenv('GITHUB_CLIENT_SECRET'),
    authorize_url='https://github.com/login/oauth/authorize',
    authorize_params=None,
    access_token_url='https://github.com/login/oauth/access_token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri=os.getenv('GITHUB_REDIRECT_URI'),
    client_kwargs={'scope': 'user:email'},
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
reset_tokens = {}

@router.post("/register", response_model=schemas.Token)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"\n{'='*50}")
    print(f"📝 REGISTRATION ATTEMPT")
    print(f"Email: {user.email}")
    print(f"Name: {user.name}")
    print(f"{'='*50}\n")
    
    # Check if user exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        print(f"❌ User already exists!")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Validate password length
    if len(user.password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long (max 72 characters)"
        )
    
    # Create new user
    try:
        print(f"🔐 Hashing password...")
        hashed_password = security.get_password_hash(user.password)
        print(f"✅ Password hashed: {hashed_password[:20]}...")
    except Exception as e:
        print(f"❌ Hash error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error hashing password: {str(e)}"
        )
    
    print(f"👤 Creating User object...")
    new_user = User(
        email=user.email,
        name=user.name,
        hashed_password=hashed_password
    )
    print(f"✅ User object created")
    
    print(f"💾 Adding to database session...")
    db.add(new_user)
    print(f"✅ Added to session")
    
    try:
        print(f"💾 Committing to database...")
        db.commit()
        print(f"✅ COMMIT SUCCESSFUL!")
        
        print(f"🔄 Refreshing user object...")
        db.refresh(new_user)
        print(f"✅ User saved with ID: {new_user.id}")
        print(f"✅ User email: {new_user.email}")
        
    except Exception as e:
        print(f"❌ DATABASE ERROR: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    # Create access token
    print(f"🔑 Creating access token...")
    access_token = security.create_access_token(data={"sub": str(new_user.id)})
    print(f"✅ Token created")
    
    print(f"\n{'='*50}")
    print(f"✅ REGISTRATION COMPLETE")
    print(f"User ID: {new_user.id}")
    print(f"{'='*50}\n")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, db: Session = Depends(get_db)):
    # Find user
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not security.verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=schemas.UserResponse)
def get_current_user(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    payload = security.decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/forgot-password", response_model=schemas.PasswordResetResponse)
async def forgot_password(request: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    """Request password reset"""
    
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success (security: don't reveal if email exists)
    if not user:
        return {"message": "If that email exists, a reset link has been sent."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store token with expiration (1 hour)
    reset_tokens[reset_token] = {
        "email": user.email,
        "expires": datetime.utcnow() + timedelta(hours=1)
    }
    
    print(f"🔑 Reset token generated for {user.email}")
    print(f"🔗 Token: {reset_token}")
    
    # Send email
    email_sent = await send_reset_email(user.email, reset_token)
    
    if not email_sent:
        print(f"⚠️  Email failed, but token is valid: {reset_token}")
    
    return {"message": "If that email exists, a reset link has been sent."}


@router.post("/reset-password", response_model=schemas.PasswordResetResponse)
def reset_password(request: schemas.PasswordReset, db: Session = Depends(get_db)):
    """Reset password with token"""
    
    # Validate token
    token_data = reset_tokens.get(request.token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check expiration
    if datetime.utcnow() > token_data["expires"]:
        # Remove expired token
        del reset_tokens[request.token]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token has expired"
        )
    
    # Get user
    user = db.query(User).filter(User.email == token_data["email"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters"
        )
    
    if len(request.new_password) > 72:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is too long (max 72 characters)"
        )
    
    # Update password
    user.hashed_password = security.get_password_hash(request.new_password)
    db.commit()
    
    # Remove used token
    del reset_tokens[request.token]
    
    print(f"✅ Password reset successful for {user.email}")
    
    return {"message": "Password has been reset successfully"}

@router.get("/google/login")
async def google_login(request: Request):
    """Redirect to Google OAuth"""
    redirect_uri = "http://localhost:8000/api/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    try:
        # Get token from Google
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info
        user_info = token.get('userinfo')
        if not user_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from Google"
            )
        
        email = user_info.get('email')
        name = user_info.get('name')
        google_id = user_info.get('sub')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )
        
        print(f"🔐 Google OAuth login: {email}")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            if user.name != name:
                user.name = name
                db.commit()
                print(f"✅ Updated user name: {email}")
            print(f"✅ Existing user logged in: {email}")
        else:
            # Create new user
            # Generate a random password (they'll use OAuth to login)
            random_password = secrets.token_urlsafe(32)
            hashed_password = security.get_password_hash(random_password)
            
            user = User(
                email=email,
                name=name,
                hashed_password=hashed_password,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"✅ New user created via Google: {email}")
        
        # Create access token
        access_token = security.create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/?oauth_token={access_token}&oauth_email={email}&oauth_name={name}"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        print(f"❌ Google OAuth error: {e}")
        import traceback
        traceback.print_exc()
        error_url = f"http://localhost:3000/?oauth_error={str(e)}"
        return RedirectResponse(url=error_url)
    
@router.get("/github/login")
async def github_login(request: Request):
    """Redirect to GitHub OAuth"""
    redirect_uri = "http://localhost:8000/api/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/github/callback")
async def github_callback(request: Request, db: Session = Depends(get_db)):
    """Handle GitHub OAuth callback"""
    try:
        # Get token from GitHub
        token = await oauth.github.authorize_access_token(request)
        
        # Get user info from GitHub
        resp = await oauth.github.get('https://api.github.com/user', token=token)
        user_info = resp.json()
        
        # GitHub doesn't always provide email in the user endpoint
        # We need to fetch it separately
        email = user_info.get('email')
        
        if not email:
            # Fetch email from separate endpoint
            email_resp = await oauth.github.get('https://api.github.com/user/emails', token=token)
            emails = email_resp.json()
            # Get primary verified email
            for email_data in emails:
                if email_data.get('primary') and email_data.get('verified'):
                    email = email_data.get('email')
                    break
        
        name = user_info.get('name') or user_info.get('login')
        github_id = user_info.get('id')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by GitHub. Please make your email public in GitHub settings."
            )
        
        print(f"🔐 GitHub OAuth login: {email}")
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            if user.name != name:
                user.name = name
                db.commit()
                print(f"✅ Updated user name: {email}")
            print(f"✅ Existing user logged in: {email}")
        else:
            # Create new user
            # Generate a random password (they'll use OAuth to login)
            random_password = secrets.token_urlsafe(32)
            hashed_password = security.get_password_hash(random_password)
            
            user = User(
                email=email,
                name=name,
                hashed_password=hashed_password,
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            print(f"✅ New user created via GitHub: {email}")
        
        # Create access token
        access_token = security.create_access_token(data={"sub": str(user.id)})
        
        # Redirect to frontend with token
        frontend_url = f"http://localhost:3000/?oauth_token={access_token}&oauth_email={email}&oauth_name={name}"
        
        return RedirectResponse(url=frontend_url)
        
    except Exception as e:
        print(f"❌ GitHub OAuth error: {e}")
        import traceback
        traceback.print_exc()
        error_url = f"http://localhost:3000/?oauth_error={str(e)}"
        return RedirectResponse(url=error_url)

# Helper function to get current user (use this in protected routes)
def get_current_user_dependency(token: str = Depends(security.oauth2_scheme), db: Session = Depends(get_db)):
    return get_current_user(token, db)

# Optional auth - for routes that work with or without login
security_optional = HTTPBearer(auto_error=False)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
    db: Session = Depends(get_db)
):
    """Get current user if token exists and is valid, otherwise return None"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        payload = security.decode_token(token)
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(User).filter(User.id == int(user_id)).first()
        return user
    except Exception as e:
        print(f"Error getting optional user: {e}")
        return None