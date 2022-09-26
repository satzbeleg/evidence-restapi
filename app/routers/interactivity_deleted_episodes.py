from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from .auth_email import get_current_user
from ..cqlconn import CqlConn
import gc
import logging
import uuid

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
        # prepare insert statement
        stmt = session.prepare("""
        INSERT INTO evidence.interactivity_convergence
        (episode_id, training_score_history, model_score_history, displayed,
         user_id, sentence_text, headword)
        VALUES (?, ?, ?, ?, ?, ?, ?) IF NOT EXISTS;
        """)

        # init batch statements
        headwords = set([episode['headword'] for episode in data])
        batch_stmts = {}
        for headword in headwords:
            batch_stmts[headword] = cas.query.BatchStatement(
                consistency_level=cas.query.ConsistencyLevel.ANY)

        # read data and add to batch statement
        for episode in data:
            batch_stmts[episode['headword']].add(stmt, [
                uuid.uuid4(),  # episode_id
                episode['training-score-history'],
                episode['model-score-history'],
                episode['displayed'],
                uuid.UUID(user_id),
                episode['sentence-text'],
                episode['headword']
            ])

        # excute statments
        for headword in headwords:
            session.execute_async(batch_stmts[headword])

        # confirm exampleIDs for deletion within the app
        stored_example_ids = [episode['example-id'] for episode in data]
        flag = True
    except Exception as err:
        print(err)
        flag = False
        stored_sentids = []
    finally:
        gc.collect()
        return {
            'status': 'success' if flag else 'failed',
            'stored-example-ids': stored_example_ids}
