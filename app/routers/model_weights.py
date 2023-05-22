from fastapi import APIRouter, Depends
from typing import Dict, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import cassandra as cas
import cassandra.query
import gc
import logging
import datetime
import uuid
import json

# start logger
logger = logging.getLogger(__name__)

# POST /variation/serialized-features
router = APIRouter()


# connect to Cassandra DB
conn = CqlConn()
session = conn.get_session()


@router.post("/save")
async def save_model_weights(data: Dict[str, Any],
                             user_id: str = Depends(get_current_user)
                             ) -> dict:
    try:
        # prepare insert statement
        stmt = session.prepare(f"""
        INSERT INTO {session.keyspace}.model_weights
        (user_id, updated_at, weights)
        VALUES (?, ?, ?) IF NOT EXISTS;
        """)

        print(data['weights'], type(data['weights']))

        # init batch statements
        res = session.execute(stmt, [
            uuid.UUID(user_id), 
            datetime.datetime.now(), 
            json.dumps(data['weights'])
        ])
        flag = res[0].applied
    except Exception as err:
        logger.error(err)
        flag = False
    finally:
        gc.collect()
        return {'status': 'success' if flag else 'failed'}


@router.post("/load")
async def load_model_weights(user_id: str = Depends(get_current_user)
                             ) -> dict:
    try:
        # prepare statement
        stmt = cas.query.SimpleStatement(f"""
            SELECT updated_at, weights
            FROM {session.keyspace}.model_weights
            WHERE user_id=%s LIMIT 1;
            """)
        # find last model weights
        timestamp, weights = None, None
        for row in session.execute(stmt, [uuid.UUID(user_id)]):
            timestamp = row.updated_at
            weights = json.loads(row.weights)
            break
        # delete
        del stmt
        gc.collect()
    except Exception as err:
        logger.error(err)
        gc.collect()
        return {"status": "failed"}

    if weights is None:
        return {"status": "no-data"}

    # done
    return {
        'status': 'success',
        'timestamp': timestamp,
        'weights': weights
    }


@router.post("/load-all")
async def load_model_weights(user_id: str = Depends(get_current_user)
                             ) -> dict:
    try:
        # prepare statement
        stmt = cas.query.SimpleStatement(f"""
            SELECT updated_at, weights
            FROM {session.keyspace}.model_weights
            WHERE user_id=%s ;
            """)
        # find last model weights
        results = []
        for row in session.execute(stmt, [uuid.UUID(user_id)]):
            results.append({
                'updated_at': row.updated_at, 
                'weights': json.loads(row.weights)
            })
        # delete
        del stmt
        gc.collect()
    except Exception as err:
        logger.error(err)
        gc.collect()
        return {"status": "failed"}

    if len(results) == 0:
        return {"status": "no-data"}

    # done
    return {
        'status': 'success',
        'data': results
    }
