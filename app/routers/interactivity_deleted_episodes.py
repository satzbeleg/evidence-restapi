from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from .auth_email import get_current_user

import psycopg2
from ..config import config_ev_psql
import gc
import json

router = APIRouter()


@router.post("")
async def save_deleted_episodes(data: Dict[str, Any],
                                user_id: str = Depends(get_current_user)
                                ) -> dict:
    try:
        # connect to DB
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()

        # generate query string and run query
        queryvalues = b",".join(cur.mogrify(
            "(%s::uuid, %s::uuid, %s::real[], %s::real[], %s::boolean[])", [
                user_id,
                sent_id,
                x["training_score_history"],
                x["model_score_history"],
                x["displayed"]
            ]) for sent_id, x in data.items()).decode("utf-8")

        # run insert query
        cur.execute((
            "INSERT INTO evidence.interactivity_deleted_episodes( "
            " user_id, sentence_id, training_score_history, model_score_history, displayed "
            f") VALUES {queryvalues} "
            "ON CONFLICT DO NOTHING "
            "RETURNING sentence_id;"))

        stored_sentids = cur.fetchall()
        flag = True
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        flag = False
        stored_sentids = []
    finally:
        gc.collect()
        return {
            'status': 'success' if flag else 'failed',
            'stored-sentids': stored_sentids}

