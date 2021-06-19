from fastapi import APIRouter, HTTPException, Depends
from typing import List, Any
from .auth_email import get_current_user

import psycopg2
from ..config import config_auth_psql
import gc
import json


# Summary
#   GET     n.a.
#   POST    /bestworst/evaluations
#               Save a list of evaluated example sets
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


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
                  "lemmata": ["Stichwort1", "Keyword2"],
                  "event-history": [{"events": "many"}, {"and": "again"}],
                  "state-sentid-map": {"idx0": "stateA", "idx1": "stateB"} }]'

    Notes:
    ------
    - We are not doing any post-processing within the API or database. It's
        expected that the WebApp sends the data as it should be stored in
        the database.
    - Use a bulk insert statement by creating one big SQL query string for
        1 commit instead of using psycopg2's `cur.executemany` what would
        loop through N commits (see https://stackoverflow.com/a/10147451)
    - How to JSON: https://www.psycopg.org/docs/extras.html#json-adaptation
    """
    try:
        # connect to DB
        conn = psycopg2.connect(**config_auth_psql)
        cur = conn.cursor()

        # generate query string and run query
        queryvalues = b",".join(cur.mogrify(
            (
                "(%s::uuid, %s::text, %s::uuid, %s::text[],"
                "%s::jsonb, %s::jsonb, %s::jsonb)"
            ), [
                user_id,
                exset['ui-name'],
                exset['set-id'],
                exset['lemmata'],
                json.dumps(exset['event-history']),
                json.dumps(exset['state-sentid-map']),
                json.dumps(exset['tracking-data'])
            ]) for exset in data).decode("utf-8")
        # print(queryvalues)

        cur.execute((
            "INSERT INTO evidence.evaluated_bestworst(user_id, ui_name, "
            "set_id, lemmata, event_history, state_sentid_map, tracking_data "
            f") VALUES {queryvalues} "
            "ON CONFLICT DO NOTHING "
            "RETURNING set_id;"))

        stored_setids = cur.fetchall()
        flag = True
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        flag = False
        stored_setids = []
    finally:
        gc.collect()
        return {
            'status': 'success' if flag else 'failed',
            'stored-setids': stored_setids}
