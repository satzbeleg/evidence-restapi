from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
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

import smtplib 
from email.message import EmailMessage
from ..config import cfg_mailer


# Settings
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


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
                "SELECT auth.email_isactive(%s::uuid);", [user_id])
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
        except Exception:
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
        except Exception:
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
        except Exception:
            user_id = None
        finally:
            gc.collect()
            return user_id


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
    # validate email/password in PSQL DB
    db = PsqlDb(config_auth_psql)
    # validate email/password
    user_id = db.validate_user(form_data.username, form_data.password)

    # throw an exception
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
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

    # Create E-Mail object
    msg = EmailMessage()
    URL = f"{cfg_mailer['RESTAPI_PUBLIC_URL']}/v1/auth/verify/{verify_token}"
    msg.set_content((
        "Please confirm your registration:\n"
        f"<a href='{URL}'>{URL}</a>"
    ))
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



# Help
# - https://fastapi.tiangolo.com/tutorial/security/simple-oauth2/
# - https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
# - https://github.com/frankie567/fastapi-users/issues/106#issuecomment-691427853

