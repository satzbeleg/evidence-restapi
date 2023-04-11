from fastapi import APIRouter, Depends
from typing import Dict, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import cassandra as cas
import cassandra.query
import gc
import logging
import time
import json

# start logger
logger = logging.getLogger(__name__)

# POST /variation/serialized-features
router = APIRouter()


# connect to Cassandra DB
conn = CqlConn()
session = conn.get_session()


# Store this in a user session
paging_states = {}


def delete_old_paging_states():
    """Delete old paging states"""
    global paging_states
    for user_id in paging_states:
        for headword in paging_states[user_id]:
            d = time.time() - paging_states[user_id][headword]['timestamp']
            if d > 86400:
                del paging_states[user_id][headword]
    gc.collect()


@router.post("")
async def get_serialized_features(params: Dict[str, Any],
                                  user_id: str = Depends(get_current_user)
                                  ) -> dict:
    """Retrieve serialized features from database

    Parameters:
    -----------
    params: List[Any]
        Settings for data retrieval, pre- and post-processing

        'headword' : str
            The headword to retrieve features for
        'limit' : int
            Maximum number of sentences to retrieve from CQL on 1 page
        'reset-pagination' : bool
            Reset the pagination state
        

    user_id: str
        The UUID4 user_id stored in the JWT token.
        See `app/routers/token.py:get_current_user`

    Examples:
    ---------
    TOKEN="..."
    curl -X POST "http://localhost:55017/v1/serialized-features" \
        -H  "accept: application/json" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer ${TOKEN}" \
        -d '{"headword": "Stichwort", "limit": 100}'

    Notes:
    ------
    - We are not doing any post-processing within the API or database. It's
        expected that the WebApp sends the data as it should be stored in
        the database.
    - How to JSON: https://www.psycopg.org/docs/extras.html#json-adaptation
    """
    # read headword
    headword = params.get('headword')
    if headword is None:
        return {"status": "failed", "num": 0,
                "msg": f"No headword='{headword}' provided"}

    # max number of sentences to fetch per page
    limit = params.get("limit", 500)

    # init pagination
    global paging_states
    if paging_states.get(user_id) is None:
        paging_states[user_id] = {}
    if paging_states[user_id].get(headword) is None:
        paging_states[user_id][headword] = {
            'paging_state': None, 'timestamp': time.time()}

    # reset pagination
    if params.get("reset-pagination", False):
        paging_states[user_id][headword] = {
            'paging_state': None, 'timestamp': time.time()}

    # download data
    try:
        # prepare statement
        stmt = cas.query.SimpleStatement(f"""
            SELECT headword, example_id, sentence, sent_id
                 , spans, annot, biblio, license, score
                 , feats1
                 , feats2, feats3, feats4, feats5
                 , feats6, feats7, feats8, feats9
                 , feats12, feats13, feats14
                 , hashes15, hashes16, hashes18
            FROM {session.keyspace}.tbl_features
            WHERE headword='{headword}';
            """, fetch_size=limit)

        # read fetched rows
        examples = []

        # read async fetched rows
        def process_results(results):
            for row in results:
                examples.append({
                    "headword": row.headword, 
                    "example_id": str(row.example_id), 
                    "sentence": row.sentence, 
                    "sentence_id": str(row.sent_id), 
                    "spans": json.dumps(row.spans), 
                    "annot": row.annot, 
                    "biblio": row.biblio, 
                    "license": row.license, 
                    "score": row.score,
                    "feats1": row.feats1,
                    "feats2": row.feats2,
                    "feats3": row.feats3,
                    "feats4": row.feats4,
                    "feats5": row.feats5,
                    "feats6": row.feats6,
                    "feats7": row.feats7,
                    "feats8": row.feats8,
                    "feats9": row.feats9,
                    "feats12": row.feats12,
                    "feats13": row.feats13,
                    "feats14": row.feats14,
                    "hashes15": row.hashes15,
                    "hashes16": row.hashes16,
                    "hashes18": row.hashes18,
                })

        # download 1 page of 'limit' sentences
        future = session.execute_async(
            stmt,
            paging_state=paging_states[user_id][headword]['paging_state'])
        future.add_callback(process_results)
        results = future.result()

        # update paging state
        paging_states[user_id][headword] = {
            'paging_state': results.paging_state, 'timestamp': time.time()}
        delete_old_paging_states()
        # print(paging_states, results.paging_state)

        # delete
        del stmt
        gc.collect()
    except Exception as err:
        logger.error(err)
        gc.collect()
        return {"status": "failed", "num": 0, "error": err,
                "msg": "Unknown error"}

    if len(examples) == 0:
        return {"status": "failed", "num": 0,
                "msg": "No sentence examples"}

    # done
    return {
        'status': 'success',
        'num': len(examples),
        'examples': examples
    }
