import traceback
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Depends, HTTPException, status, Request, Security
from jose import jwt, JWTError
from settings import settings
from schemas import UserLogin, UserCreate, UserResponse, Token, EventResponse, EventCreate, UserDelete, AdminUserResponse, Userupdate, EventUpdate
from common import logger
import ops
import secrets
from passlib.context import CryptContext
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from slowapi.errors import RateLimitExceeded
import warnings
warnings.filterwarnings(action='ignore')

# FastAPI App
app = FastAPI(title=settings.APP_TITLE,
              description=settings.APP_DESCRIPTION,
              version=settings.APP_VERSION,
              docs_url=settings.DOCS_URL,
              redoc_url=settings.REDOC_URL,
              openapi_url=settings.OPENAPI_URL
              )


# Configure Limiter (Rate limit based on IP address)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Custom rate limit exceeded response
@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        content={"error": "Rate limit exceeded. Please try again later."},
        status_code=429
    )



def verify_token(api_key: str = Security(ops.oauth2_scheme)):
    """Verify and decode JWT token from the Authorization header."""
    try:
        scheme, token = api_key.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")

        payload = jwt.decode(token, ops.SECRET_KEY, algorithms=[ops.ALGORITHM])
        username: str = payload.get("username")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token format")


@app.get("/admintoken")
async def read_users_me(token: str = Depends(ops.oauth2_scheme)):
    return {"message": "You are authenticated!", "token": token}


@app.post("/login", response_model=Token, tags=["User Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def login(user: UserLogin, request: Request):
    status, role = ops.authenticate_user(user)
    if not status:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = ops.create_access_token(data={"username": user.username, "role": role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register", response_model=UserResponse, tags=["User Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def register_user(user: UserCreate, request: Request):
    try:
        userid = ops.register_user_ops(user, request)
        return {"message": "success", "id": userid, "username": user.ContactNumber, "email": user.email,
                "role": "attendee"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "id": -1, "username": user.ContactNumber, "email": user.email,
                "role": "attendee"}


@app.post("/create_user", response_model=UserResponse, tags=["Admin"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def create_user(user: UserCreate, request: Request, admin=Depends(ops.get_current_admin)):
    try:
        userid = ops.register_user_ops(user, request)
        return {"message": "success", "id": userid, "username": user.username, "email": user.email, "role": "attendee"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "id": -1, "username": user.username, "email": user.email,
                "role": ""}


@app.delete("/users/{user_id}", tags=["Admin"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def delete_user(user: UserDelete, request: Request, admin=Depends(ops.get_current_admin)):
    """Delete a user by ID (Admin only)."""
    try:
        res = ops.delete_user_by_admin(user.username)
        logger.warning(f"user {user.username} deleted by admin, {res}")
        return {"message": "success", "res": f"User with ID {user.username} has been deleted"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "res": f"failed to delete the user {user.username}"}


@app.get("/users", tags=["Admin"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def list_users( request: Request, admin=Depends(ops.get_current_admin)):
    """Get a list of all registered users (Admin only)."""
    try:
        res = ops.get_all_user_details()
        return {"message": "success", "res": res}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "res": []}


@app.put("/users", tags=["Admin"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def update_user_role(user: Userupdate,request: Request, admin=Depends(ops.get_current_admin)):
    """Update user role (Admin only)."""
    try:
        res = ops.update_user_by_admin(user)
        return {"message": "success", "res": f"user {user.ContactNumber} info has been successfully updated"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "res": f"unable to update info for user {user.ContactNumber}"}



@app.post("/events/create", response_model=EventResponse, tags=["Event Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def create_event(event: EventCreate,request: Request, organizer=Depends(ops.get_current_organizer)):
    try:
        status, eventid = ops.create_event(event, organizer)
        if status:
            return EventResponse(
                message="success",
                id=eventid,
                organizer_id=event.userid
            )
        else:
            return JSONResponse(content={"message": "failed"}, status_code=500)
    except:
        logger.error(f"Error in creating new event from organizer {event}")
        return JSONResponse(content={"message": "failed"}, status_code=500)

@app.put("/events/update", tags=["Event Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def update_event_details(event: EventUpdate, request: Request, admin=Depends(ops.get_current_organizer)):
    try:
        res = ops.update_event_details(event)
        return {"message": "success", "res": f"event details {event} has been successfully updated {res}"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "res": f"unable to update event details."}


@app.delete("/events/delete", tags=["Event Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def delete_event(eventid: int, userid: int, request: Request, admin=Depends(ops.get_current_organizer)):
    try:
        res = ops.delete_event(eventid, userid)
        logger.warning(f"event {eventid} deleted by user, {userid} {res}")
        return {"message": "success", "res": f"event {eventid} has been deleted successfully"}
    except:
        logger.error(traceback.format_exc())
        return {"message": "failed", "res": f"unable to delete the event"}  

@app.get("/events", tags=["Event Management"])
@limiter.limit("5/minute")  # Allow 5 requests per minute
def get_events(request: Request):
    try:
        res = ops.getall_events()
        return {"message": "success", "res": res}
    except:
        return {"message": "failed", "res": []}


