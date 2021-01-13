from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import secrets
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from typing import Optional, Union, List
from datetime import datetime, timedelta

import psycopg2
from ..config import config_auth_psql
import gc


# Settings
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# How to create a SECRET_KEY: `openssl rand -hex 32`
SECRET_KEY = secrets.token_hex(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# TODO: Replaces this with an actual database
#
# Hash a new password
#   from passlib.context import CryptContext
#   pwctx = CryptContext(schemes=["sha512_crypt"], deprecated="auto")
#   hashed_pw = pwctx.hash(plain_pw)
#
local_users_db = {
    "testuser0": {
        "username": "testuser0",
        "hashed_password": (  # "secret"
            "$6$rounds=656000$LM/2/io2noVIc/Al$CamNMiA5vuDxHigTbN3XhB1o5jXFt"
            "E/Jwj0Y2Qz/JxToOJQT1iSG6Ixjfbj5tsgTgTVqjQgdXpjDatlCMWEdd1"),
        "disabled": False,
    },
    "testuser1": {
        "username": "testuser1",
        "hashed_password": (  # "secret"
            "$6$rounds=656000$LM/2/io2noVIc/Al$CamNMiA5vuDxHigTbN3XhB1o5jXFt"
            "E/Jwj0Y2Qz/JxToOJQT1iSG6Ixjfbj5tsgTgTVqjQgdXpjDatlCMWEdd1"),
        "disabled": False,
    }
}


#
# pydantic data schemes
#
class UserMeta(BaseModel):
    username: str
    isactive: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


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

    def validate_user(self, username, plain_password) -> bool:
        # retrieve `hashed_password` from local dict database
        # return `false` if `username` or `hashed_password` does not exist
        try:
            hashed_password = self.local_user_db[username]['hashed_password']
        except KeyError:
            return False
        # compare supplied `plain_password` with the stored password hash
        return self.pwctx.verify(plain_password, hashed_password)

    def is_active_user(self, username):
        try:
            return not self.local_user_db[username]['disabled']
        except KeyError:
            return False


class PsqlDb(object):
    def __init__(self, cfg_psql: dict):
        self.cfg_psql = cfg_psql

    def is_configured(self):
        return True if self.cfg_psql else False

    def validate_user(self, username, plain_password) -> bool:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute("SELECT auth.validate_user(%s, %s);",
                        [username, plain_password])
            isvalid = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception:
            isvalid = False
        finally:
            gc.collect()
            return isvalid

    def is_active_user(self, username) -> bool:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute("SELECT auth.is_active_user(%s);", [username])
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
        SECRET_KEY,
        algorithm=ALGORITHM)

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

    # read the `username` from token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # check if the token's username exists in the PSQL DB (isactive)
    db = PsqlDb(config_auth_psql)
    if db.is_active_user(username):
        return username
    # check if the token's username is locally defined user (isactive)
    db2 = LocalDb(local_users_db)
    if db2.is_active_user(username):
        return username
    # otherwise
    raise HTTPException(status_code=400, detail="Inactive user")


# Requires: ACCESS_TOKEN_EXPIRE_MINUTES, authenticate_user
@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    # validate username/password in PSQL DB
    username = None
    db = PsqlDb(config_auth_psql)
    if db.validate_user(form_data.username, form_data.password):
        username = form_data.username
    else:
        # try locally defined user
        db2 = LocalDb(local_users_db)
        if db2.validate_user(form_data.username, form_data.password):
            username = form_data.username

    # throw an exception
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"sub": username},
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
