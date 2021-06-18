from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from ..config import config_auth_token

from typing import Optional, Union, List
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
psycopg2.extras.register_uuid()  # to process UUIDs
from ..config import config_auth_psql
import gc
import uuid


# Settings
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# TODO: Replaces this with an actual database
#
# Hash a new password
#   from passlib.context import CryptContext
#   pwctx = CryptContext(schemes=["sha512_crypt"], deprecated="auto")
#   hashed_pw = pwctx.hash(plain_pw)
#
local_users_db = [
    {
        "user_id": "3d376550-5265-4830-9812-5e9a84cdfa29",
        "username": "testuser0",
        "hashed_password": (  # "secret"
            "$6$rounds=656000$LM/2/io2noVIc/Al$CamNMiA5vuDxHigTbN3XhB1o5jXFt"
            "E/Jwj0Y2Qz/JxToOJQT1iSG6Ixjfbj5tsgTgTVqjQgdXpjDatlCMWEdd1"),
        "isactive": True,
    },
    {
        "user_id": "1faeb6bc-11e6-449b-a0a0-3354249176a9",
        "username": "testuser1",
        "hashed_password": (  # "secret"
            "$6$rounds=656000$LM/2/io2noVIc/Al$CamNMiA5vuDxHigTbN3XhB1o5jXFt"
            "E/Jwj0Y2Qz/JxToOJQT1iSG6Ixjfbj5tsgTgTVqjQgdXpjDatlCMWEdd1"),
        "isactive": True,
    }
]


#
# pydantic data schemes
#
class UserMeta(BaseModel):
    user_id: str
    isactive: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


# class TokenData(BaseModel):
#    user_id: Optional[str] = None


#
# password handling
# - we use "sha512_crypt" for Linux servers ("bcrypt" is for BSD)
# - https://passlib.readthedocs.io/en/stable/narr/quickstart.html
#
# localdb = LocalDb(local_users_db)
#
class LocalDb(object):
    def __init__(self, local_user_db: dict = {}):
        self.pwctx = CryptContext(schemes=["sha512_crypt"], deprecated="auto")
        self.local_user_db = local_user_db

    def is_configured(self):
        return True if self.local_user_db else False

    def validate_user(self, username, plain_password) -> uuid.UUID:
        # retrieve `hashed_password` from local dict database
        # return `false` if `username` or `hashed_password` does not exist
        hashed_password = None
        for entry in self.local_user_db:
            if entry.get('username') == username:
                hashed_password = entry.get('hashed_password')
        if hashed_password is None:
            return None
        # compare supplied `plain_password` with the stored password hash
        if self.pwctx.verify(plain_password, hashed_password):
            for entry in self.local_user_db:
                if entry.get('username') == username:
                    if entry.get('hashed_password') == hashed_password:
                        return entry.get('user_id')
        return None

    def is_active_user(self, user_id: uuid.UUID) -> bool:
        for entry in self.local_user_db:
            if entry.get('user_id') == user_id:
                return entry.get('isactive')
        return None


class PsqlDb(object):
    def __init__(self, cfg_psql: dict):
        self.cfg_psql = cfg_psql

    def is_configured(self):
        return True if self.cfg_psql else False

    def validate_user(self, username, plain_password) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.validate_username_password2(%s::text, %s::text);",
                [username, plain_password])
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
            user_id = str(uuid.UUID(str(user_id)))  # trigger Error or not
        except Exception:
            user_id = None
        finally:
            gc.collect()
            return user_id

    def is_active_user(self, user_id: uuid.UUID) -> bool:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.username_isactive(%s::uuid);", [user_id])
            isactive = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception:
            isactive = False
        finally:
            gc.collect()
            return isactive


# Requires: SECRET_KEY, ALGORITHM
def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode,
        config_auth_token['SECRET_KEY'],
        algorithm=config_auth_token['ALGORITHM']
    )

    return encoded_jwt


# Requires: SECRET_KEY, ALGORITHM
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserMeta:
    """Get meta information about a user
    """
    # specify a general exception
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"})

    # read the `user_id` from token
    try:
        payload = jwt.decode(
            token, config_auth_token['SECRET_KEY'], 
            algorithms=[config_auth_token['ALGORITHM']]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception

    # check if the token's user_id exists in the PSQL DB (isactive)
    db = PsqlDb(config_auth_psql)
    if db.is_active_user(user_id):
        return user_id
    # check if the token's user_id is locally defined user (isactive)
    db2 = LocalDb(local_users_db)
    if db2.is_active_user(user_id):
        return user_id
    # otherwise
    raise HTTPException(status_code=400, detail="Inactive user")


# Requires: TOKEN_EXPIRY, authenticate_user
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    # validate username/password in PSQL DB
    db = PsqlDb(config_auth_psql)
    user_id = db.validate_user(form_data.username, form_data.password)

    # try locally defined user
    if user_id is None:
        db2 = LocalDb(local_users_db)
        user_id = db2.validate_user(form_data.username, form_data.password)

    # throw an exception
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=config_auth_token['TOKEN_EXPIRY'])

    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


"""
@router.get("/user")
async def read_users_me(current_user: UserMeta = Depends(get_current_user)):
    return current_user


@router.get("/user/items/")
async def read_own_items(current_user: UserMeta = Depends(get_current_user)):
    return [{"item_id": "Foo", "owner": current_user.username}]
"""


# Help
# - https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
# - https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
