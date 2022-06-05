from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import cassandra as cas
import cassandra.query
import uuid
import gc
import json


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


@router.post("")
async def save_evaluated_examplesets(data: List[Any],
                                     user_id: str = Depends(get_current_user)
                                     ) -> dict:
    """Save evaluated example sets to database

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
        curl -X POST "http://localhost:55017/v1/bestworst/evaluations" \
            -H  "accept: application/json" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${TOKEN}" \
            -d '[{"set-id": "147a6a02-2714-430a-a906-bdccc0c72b36",
                  "ui-name": "bestworst456",
                  "headword": "Stichwort",
                  "event-history": [{"events": "many"}, {"and": "again"}],
                  "state-sentid-map": {"idx0": "stateA", "idx1": "stateB"} }]'

    Notes:
    ------
    - We are not doing any post-processing within the API or database. It's
        expected that the WebApp sends the data as it should be stored in
        the database.
    - How to JSON: https://www.psycopg.org/docs/extras.html#json-adaptation
    """
    try:
        # prepare insert statement
        stmt = session.prepare("""
INSERT INTO evidence.evaluated_bestworst
(set_id, user_id, ui_name,
 headword, event_history, state_sentid_map, tracking_data)
VALUES (?, ?, ?, ?, ?, ?, ?) IF NOT EXISTS;
        """)

        # init batch statements
        headwords = set([exset['headword'] for exset in data])
        batch_stmts = {}
        for headword in headwords:
            batch_stmts[headword] = cas.query.BatchStatement(
                consistency_level=cas.query.ConsistencyLevel.ANY)

        # read data and add to batch statement
        for exset in data:
            batch_stmts[exset['headword']].add(stmt, [
                uuid.UUID(exset['set-id']),
                uuid.UUID(user_id),
                exset['ui-name'],
                exset['headword'],
                json.dumps(exset['event-history']),
                json.dumps(exset['state-sentid-map']),
                json.dumps(exset['tracking-data'])
            ])
        # excute statments
        for headword in headwords:
            session.execute_async(batch_stmts[headword])

        # confirm setIDs for deletion within the app
        stored_setids = [exset['set-id'] for exset in data]
        flag = True
    except Exception as err:
        print(err)
        stored_setids = []
        flag = False
    finally:
        gc.collect()
        return {
            'status': 'success' if flag else 'failed',
            'stored-setids': stored_setids}
