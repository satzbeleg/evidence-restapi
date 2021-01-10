from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
# from pydantic import BaseModel
from .token import get_current_user

import psycopg2
from ..config import config_auth_psql
import gc
import json


# Summary
#   GET     /bestworst/{n_sents}/{m_sets}
#               Return M sets of N random sentences
#   POST    /bestworst/evaluations
#               Save a list of evaluated example sets
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


@router.post("")
async def save_evaluated_examplesets(data: List[Any],
                                     username: str = Depends(get_current_user)
                                     ) -> dict:
    """Save evaluated example sets to database

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
            "(%s::text, %s::text, %s::uuid, %s::text[], %s::jsonb, %s::jsonb)", [
                username, exset['ui-name'], exset['set-id'], exset['lemmata'],
                json.dumps(exset['event-history']), json.dumps(exset['state-sentid-map'])
            ]) for exset in data).decode("utf-8")

        cur.execute((
            "INSERT INTO evidence.evaluated_bestworst(username, ui_name, "
            "set_id, lemmata, event_history, state_sentid_map "
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
