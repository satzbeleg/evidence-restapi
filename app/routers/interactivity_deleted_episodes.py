from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import gc
import logging

# start logger
logger = logging.getLogger(__name__)

# POST /interactivity/deleted-episodes with params
router = APIRouter()

# connect to Cassandra DB
conn = CqlConn()
session = conn.get_session()


@router.post("")
async def save_deleted_episodes(data: Dict[str, Any],
                                user_id: str = Depends(get_current_user)
                                ) -> dict:
    try:
        # connect to Cassandra DB
        session = CqlConn()

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
            "   user_id, sentence_id, training_score_history, "
            "   model_score_history, displayed "
            f") VALUES {queryvalues} "
            "ON CONFLICT DO NOTHING "
            "RETURNING sentence_id;"))

        # excute statments
        for headword in headwords:
            session.execute_async(batch_stmts[headword])

        # confirm setIDs for deletion within the app
        stored_setids = [exset['set-id'] for exset in data]
        flag = True
    except Exception as err:
        print(err)
        flag = False
        stored_sentids = []
    finally:
        gc.collect()
        return {
            'status': 'success' if flag else 'failed',
            'stored-sentids': stored_sentids}
