from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import cassandra as cas
import cassandra.query
import gc
import logging
import time

# start logger
logger = logging.getLogger(__name__)

# Summary
#   GET     n.a.
#   POST    /bestworst/evaluations
#               Save a list of evaluated example sets
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


# connect to Cassandra DB
conn = CqlConn()
session = conn.get_session()


# Store this in a user session
# paging_states[user_id][headword] = {'paging_state': paging_state, 'timestamp': time.time()}
# paging_state = None
# old_headword = ""
paging_states = {}

def delete_old_paging_states():
    """Delete old paging states"""
    global paging_states
    for user_id in paging_states:
        for headword in paging_states[user_id]:
            if (time.time() - paging_states[user_id][headword]['timestamp']) > 86400:
                del paging_states[user_id][headword]
    gc.collect()


@router.post("")
async def get_serialized_features(data: Dict[str, Any],
                                  user_id: str = Depends(get_current_user)
                                  ) -> dict:
    """Retrieve serialized features from database

    Parameters:
    -----------
    data: List[Any]
        A list of serialized JSON objects.
        (We don't check it further with pydantic as the event history might
         change depending of UI.)

    user_id: str
        The UUID4 user_id stored in the JWT token.
        See `app/routers/token.py:get_current_user`

    Examples:
    ---------
    TOKEN="..."
    curl -X POST "http://localhost:55017/v1/variation/serialized-features" \
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
    headword = data.get('headword')
    if headword is None:
        return {"status": "failed", "num": 0,
                "msg": f"No headword='{headword}' provided"}

    # max number of sentences
    limit = data.get("limit", 500)

    # reset pagination
    global paging_states
    if paging_states.get(user_id) is None:
        paging_states[user_id] = {}
    if paging_states[user_id].get(headword) is None:
        paging_states[user_id][headword] = {'paging_state': None, 'timestamp': time.time()}

    # download data
    try:
        # prepare statement
        stmt = cas.query.SimpleStatement(f"""
            SELECT sentence
                 , biblio
                 , score
                 , feats1
                 , feats2, feats3, feats4, feats5
                 , feats6, feats7, feats8, feats9
                 , feats12, feats13, feats14
                 , hashes15, hashes16, hashes18
            FROM {session.keyspace}.tbl_features
            WHERE headword='{headword}';
            """, fetch_size=limit)

        # read fetched rows
        sentences = []
        biblio = []
        scores = []
        feats1 = []
        feats2 = []
        feats3 = []
        feats4 = []
        feats5 = []
        feats6 = []
        feats7 = []
        feats8 = []
        feats9 = []
        feats12 = []
        feats13 = []
        feats14 = []
        hashes15 = []
        hashes16 = []
        hashes18 = []

        # read async fetched rows
        def process_results(results):
            for row in results:
                sentences.append(row.sentence)
                biblio.append(row.biblio)
                scores.append(row.score)
                feats1.append(row.feats1)
                feats2.append(row.feats2)
                feats3.append(row.feats3)
                feats4.append(row.feats4)
                feats5.append(row.feats5)
                feats6.append(row.feats6)
                feats7.append(row.feats7)
                feats8.append(row.feats8)
                feats9.append(row.feats9)
                feats12.append(row.feats12)
                feats13.append(row.feats13)
                feats14.append(row.feats14)
                hashes15.append(row.hashes15)
                hashes16.append(row.hashes16)
                hashes18.append(row.hashes18)

        # download 1 page of 'limit' sentences
        future = session.execute_async(stmt, paging_state=paging_states[user_id][headword]['paging_state'])
        future.add_callback(process_results)
        results = future.result()

        # update paging state
        paging_states[user_id][headword] = {
            'paging_state': results.paging_state, 'timestamp': time.time()}
        delete_old_paging_states()
        print(paging_states, results.paging_state)

        # delete
        del stmt
        gc.collect()
    except Exception as err:
        logger.error(err)
        gc.collect()
        return {"status": "failed", "num": 0, "error": err,
                "msg": "Unknown error"}

    if len(sentences) == 0:
        return {"status": "failed", "num": 0,
                "msg": "No sentence examples"}

    # done
    return {
        'status': 'success',
        'num': len(sentences),
        'sentences': sentences,
        'biblio': biblio,
        'scores': scores,
        'feats1': feats1,
        'feats2': feats2,
        'feats3': feats3,
        'feats4': feats4,
        'feats5': feats5,
        'feats6': feats6,
        'feats7': feats7,
        'feats8': feats8,
        'feats9': feats9,
        'feats12': feats12,
        'feats13': feats13,
        'feats14': feats14,
        'hashes15': hashes15,
        'hashes16': hashes16,
        'hashes18': hashes18,
    }
