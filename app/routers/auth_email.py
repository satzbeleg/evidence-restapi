import fastapi
from fastapi import Depends
# from fastapi import APIRouter, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel
from ..config import config_auth_token

from typing import Optional, Union, List
from datetime import datetime, timedelta

import psycopg2
import psycopg2.extras
from ..config import config_auth_psql
import gc
import uuid
import logging

import smtplib
from email.message import EmailMessage
from ..config import cfg_mailer


# Settings
router = fastapi.APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
psycopg2.extras.register_uuid()  # to process UUIDs


#
# pydantic data schemes
#
class UserMeta(BaseModel):
    user_id: str
    isactive: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class GapiUserMeta(BaseModel):
    gid: str
    email: str


class PsqlDb(object):
    def __init__(self, cfg_psql: dict):
        self.cfg_psql = cfg_psql

    def is_configured(self):
        return True if self.cfg_psql else False

    def validate_user(self, email, plain_password) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.validate_email_password2(%s::text, %s::text);",
                [email, plain_password])
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
            user_id = str(uuid.UUID(str(user_id)))  # trigger Error or not
        except Exception as e:
            logging.error(e)
            user_id = None
        finally:
            gc.collect()
            return user_id

    def is_active_user(self, user_id: uuid.UUID) -> bool:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.email_isactive(%s::uuid);", [user_id])
            isactive = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception as e:
            logging.error(e)
            isactive = False
        finally:
            gc.collect()
            return isactive

    def add_new_email_account(self, email, plain_password) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.add_new_email_account(%s::text, %s::text);",
                [email, plain_password])
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception as e:
            logging.error(e)
            user_id = None
        finally:
            gc.collect()
            return user_id

    def issue_verification_token(self, user_id: uuid.UUID) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.issue_verification_token(%s::uuid);",
                [user_id])
            verify_token = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception as e:
            logging.error(e)
            verify_token = None
        finally:
            gc.collect()
            return verify_token

    def check_verification_token(self, verify_token: uuid.UUID) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.check_verification_token(%s::uuid);",
                [verify_token])
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
        except Exception as e:
            logging.error(e)
            user_id = None
        finally:
            gc.collect()
            return user_id

    def upsert_google_signin(self, gid: str, email: str) -> uuid.UUID:
        try:
            conn = psycopg2.connect(**self.cfg_psql)
            cur = conn.cursor()
            cur.execute(
                "SELECT auth.upsert_google_signin(%s::text, %s::text);",
                [gid, email])
            user_id = cur.fetchone()[0]
            conn.commit()
            cur.close()
            conn.close()
            del cur, conn
            user_id = str(uuid.UUID(str(user_id)))  # trigger Error or not
        except Exception as e:
            logging.error(e)
            user_id = None
        finally:
            gc.collect()
            return user_id


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None):
    """ Create a serialized JSON Web Token (JWT) as Access Token

    Parameters:
    -----------
    data : dict
        Payload as JSON

    expires_delta : timedelta (Default: None)
        Time till expiry, e.g. `expires_delta=timedelta(minutes=15)`

    Global Variables:
    -----------------
        config_auth_token['SECRET_KEY']
        config_auth_token['ALGORITHM']

    Return:
    -------
    encoded_jwt : str
        serialized JSON Web Token (JWT) as Access Token
    """
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


async def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Get meta information about a user

    Parameters:
    -----------
    token : str
        The decoded access token

    Global Variables:
    -----------------
        status
        oauth2_scheme
        config_auth_token['SECRET_KEY']
        config_auth_token['ALGORITHM']

    Return:
    -------
    user_id : str
        The user_id as string (not uuid.UUID)
    """
    # specify a general exception
    credentials_exception = fastapi.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
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
    except JWTError:
        raise credentials_exception

    # check if the token's user_id exists in the PSQL DB (isactive)
    db = PsqlDb(config_auth_psql)
    if db.is_active_user(user_id):
        return user_id

    # otherwise
    raise fastapi.HTTPException(status_code=400, detail="Inactive user")


@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    """ Process login data

    Parameters:
    -----------
    form_data : OAuth2PasswordRequestForm
        Contains email address (form_data.username) and 
          password (form_data.password)
    
    Global Variables:
    -----------------
        config_auth_token['TOKEN_EXPIRY']
    
    Examples:
    ---------
    curl -X POST "http://0.0.0.0:55017/v1/auth/login" \
        -H "accept: application/json" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=${EMAIL}&password=${PASSWORD}" > mytokendata
    """
    # validate email/password in PSQL DB
    db = PsqlDb(config_auth_psql)
    # validate email/password
    user_id = db.validate_user(form_data.username, form_data.password)

    # throw an exception
    if user_id is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=config_auth_token['TOKEN_EXPIRY'])

    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/register")
async def register(form_data: OAuth2PasswordRequestForm = Depends()) -> dict:
    # validate email/password in PSQL DB
    db = PsqlDb(config_auth_psql)

    # add new email/password based account
    user_id = db.add_new_email_account(form_data.username, form_data.password)
    # create a verification token
    verify_token = db.issue_verification_token(user_id)

    if verify_token is None:
        return {"status": "failed", "msg": "Cannot create token."}

    # Create E-Mail object
    msg = EmailMessage()
    URL = f"{cfg_mailer['VERIFY_PUBLIC_URL']}/v1/auth/verify/{verify_token}"
    msg.set_content(f"Please confirm your registration:\n{URL}")
    msg['Subject'] = "Please confirm your registration"
    msg['From'] = cfg_mailer["FROM_EMAIL"]
    msg['To'] = form_data.username   # Is the Email

    # Send Verification Mail
    with smtplib.SMTP(cfg_mailer["SMTP_SERVER"],
                      cfg_mailer["SMTP_PORT"]) as server:
        if cfg_mailer["SMTP_TLS"] is not None:
            server.starttls()
        server.login(cfg_mailer["SMTP_USER"], cfg_mailer["SMTP_PASSWORD"])
        server.send_message(msg)

    return {"status": "sucess", "msg": "Verfication mail sent."}


@router.get("/verify/{verify_token}")
async def verify(verify_token: uuid.UUID) -> dict:
    # validate email/password in PSQL DB
    db = PsqlDb(config_auth_psql)
    # check v. token
    user_id = db.check_verification_token(verify_token)
    # return the result
    if user_id is None:
        return {"status": "failed", "msg": "Invalid verification token."}
    else:
        return {"status": "success", "msg": "New account verified."}


# Requires: TOKEN_EXPIRY, authenticate_user
@router.post("/google-signin")
async def google_signin(params: GapiUserMeta) -> dict:
    # validate email/password in PSQL DB
    db = PsqlDb(config_auth_psql)
    # validate email/password
    user_id = db.upsert_google_signin(params.gid, params.email)

    # throw an exception
    if user_id is None:
        raise fastapi.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail="Cannot process Google OAuth Email and ID.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(
        minutes=config_auth_token['TOKEN_EXPIRY'])

    access_token = create_access_token(
        data={"sub": user_id},
        expires_delta=access_token_expires)

    return {"access_token": access_token, "token_type": "bearer"}
