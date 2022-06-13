from fastapi import APIRouter, HTTPException, Depends
from ..cqlconn import CqlConn
import cassandra as cas
import gc
import logging
import numpy as np

# start logger
logger = logging.getLogger(__name__)

# POST /interactivity/training-examples/{n_top}/{n_offset}
router = APIRouter()

# connect to Cassandra DB
conn = CqlConn()
session = conn.get_session()


@router.post("/{n_examples}/{n_top}/{n_offset}")
async def get_examples_with_features(n_examples: int,
                                     n_top: int,
                                     n_offset: int,
                                     params: dict) -> list:
    # read the headword key value
    if params:
        headword = params['headword']
        # exclude_deleted_ids = params.get('exclude_deleted_ids', False)
    else:
        return {"status": "failed", "msg": "Please search for the headword."}

    # query database for example items
    try:
        # prepare statement to download the whole partion
        stmt = session.prepare("""
SELECT example_id, sentence_text, headword,
  features1, features2,
  spans, sentence_id, license, initial_score
FROM examples WHERE headword=? LIMIT 10000;
        """)
        # fetch partition
        dat = session.execute(stmt, [headword])
        # read data to list of json
        items = []
        for row in dat:
            items.append({
                "id": row.example_id,
                "text": row.sentence_text,
                "spans": row.spans,
                "context": {
                    "license": row.license,
                    "sentence_id": row.sentence_id},
                "score": row.initial_score,
                "features": {
                    "semantic": row.features1,
                    "syntax": row.features2}
            })
    except cas.ReadTimeout as err:
        logger.error(f"Read Timeout problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    except Exception as err:
        logger.error(f"Unknown problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    finally:
        gc.collect()

    # sort by largest score n_top, n_offset
    if len(items) > n_top:
        items = sorted(items, key=lambda x: x["score"], reverse=True)
        items = items[(n_offset):(n_offset + n_top)]

    # abort if no query results
    if len(items) == 0:
        return {"status": "failed", "msg": "no sentences found."}

    # randomly sample items
    return np.random.choice(
        items, min(len(items), n_examples),
        replace=False).tolist()
