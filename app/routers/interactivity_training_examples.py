from fastapi import APIRouter, HTTPException, Depends
# from typing import List, Any
# from .auth_email import get_current_user
from .bestworst_samples import get_sentence_text, extract_spans

import psycopg2
from ..config import config_ev_psql
import gc
import json

router = APIRouter()


@router.post("/{n_examples}/{n_top}/{n_offset}")
async def get_examples_with_features(n_examples: int,
                                     n_top: int,
                                     n_offset: int,
                                     params: dict) -> list:
    # read the lemmata key value
    if params:
        keywords = params['lemmata']
        model_info = params.get('model_info', None)
        # exclude_deleted_ids = params.get('exclude_deleted_ids', False)
    else:
        return {"status": "failed", "msg": "Please search for a lemma."}

    # query database for example items
    try:
        # Open connection to EVIDENCE database
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()

        # Search for a specific model
        if model_info:
            querymodel = cur.mogrify(
                " WHERE model_info=%s::jsonb ",
                [json.dumps(model_info)]).decode("utf-8")
        else:
            querymodel = " ORDER BY tb.sentence_id, tb2.created_at DESC "

        # run query
        cur.execute("""
SELECT distinct on (tb.sentence_id) tb.sentence_id
     , tb.context
     , tb.score
     , tb2.feature_vectors
     , tb2.model_info
FROM (
    SELECT sentence_id, context, score
    FROM evidence.query_by_lemmata(%s::text[], %s::int, %s::int)
    ORDER BY random()
    ) tb
INNER JOIN zdlstore.feature_vectors tb2
        ON tb.sentence_id = tb2.sentence_id
""" + querymodel + " LIMIT %s ;", [keywords, n_top, n_offset, n_examples])
        items = cur.fetchall()
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        return {"status": "failed", "msg": err}
    finally:
        gc.collect()

    # abort if no query results
    if len(items) == 0:
        return {"status": "failed", "msg": "no sentences found."}

    # download sentence_text
    try:
        dbsentences = get_sentence_text([row[0] for row in items])
    except Exception as err:
        print(err)
        return {"status": "failed", "msg": err}

    # combine both sources into a list of jsons
    items2 = []
    for row in items:
        # possible error message
        text = f"SentenceID '{row[0]}' doesn't exist in the ZDLStore API."
        spans = []
        if row[0] in dbsentences:
            tmp = dbsentences.get(row[0])
            text = tmp.get('text', f"DB entry malformed for '{row[0]}'")
            spans = extract_spans(tmp.get('annotation', {}), keywords)
        # append json to array
        items2.append({
            "id": row[0],
            "text": text,
            "spans": spans,
            "context": row[1],
            "score": row[2],
            "features": row[3]
        })

    return items2
