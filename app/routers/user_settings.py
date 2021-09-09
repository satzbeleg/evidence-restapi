from fastapi import APIRouter, HTTPException, Depends
# from typing import List, Dict, Any
# from pydantic import BaseModel
from .auth_email import get_current_user

import psycopg2
import json
from ..config import config_ev_psql
import gc


# Settings
router = APIRouter()


@router.post("")
async def upsert_user_settings(settings: dict,
                               username: str = Depends(get_current_user)
                               ) -> dict:
    """ Receive user settings updates from App and store to database

    Parameters:
    -----------
    settings : dict
        The JSON with all the user settings received from the app.

    username : str (uuid.UUID4)
        User ID

    Return:
    -------
    dict
        Status message
    """
    try:
        # connect to DB
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()
        # run queries
        cur.execute(
            "SELECT evidence.upsert_user_settings(%s::text, %s::jsonb);",
            [username, json.dumps(settings)])
        flag = cur.fetchone()[0]
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        flag = False
    finally:
        gc.collect()
        return {'status': 'success' if flag else 'failed'}


@router.get("")
async def get_user_settings(username: str = Depends(get_current_user)) -> dict:
    try:
        # connect to DB
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()
        # run queries
        cur.execute('''
            SELECT settings FROM evidence.user_settings
            WHERE username=%s;''', [username])
        data = cur.fetchone()[0]
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        data = {}
    finally:
        gc.collect()
        return data
