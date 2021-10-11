from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
# from pydantic import BaseModel
from .auth_email import get_current_user

import psycopg2
import json
from ..config import config_ev_psql
import gc
import logging


# Settings
router = APIRouter()


@router.post("")
async def upsert_user_settings(settings: Dict[Any, Any] = None,
                               user_id: str = Depends(get_current_user)
                               ) -> dict:
    """ Store user settings from App into the database

    Parameters:
    -----------
    settings : dict
        The JSON with all the user settings received from the app.

    user_id : str (uuid.UUID4)
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
                "SELECT evidence.upsert_user_settings(%s::uuid, %s::jsonb);",
                [user_id, json.dumps(settings)])
        flag = cur.fetchone()[0]
        conn.commit()
            # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        logging.error(err)
        flag = False
    finally:
        gc.collect()
        return {'status': 'success' if flag else 'failed'}


@router.get("")
async def get_user_settings(user_id: str = Depends(get_current_user)) -> dict:
    """ Load user settings from the database

    Parameters:
    -----------
    user_id : str (uuid.UUID4)
        User ID

    Return:
    -------
    data : dict
        The JSON with all the user settings stored in the database
    """
    try:
        # connect to DB
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()
        # run queries
        cur.execute('''
            SELECT settings FROM evidence.user_settings
            WHERE user_id=%s::uuid;''', [user_id])
        data = cur.fetchone()[0]
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        logging.error(err)
        data = {}
    finally:
        gc.collect()
        # print("Debug:", user_id, data)
        return data
