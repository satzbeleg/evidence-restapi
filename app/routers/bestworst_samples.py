from fastapi import APIRouter, HTTPException
from typing import List, Tuple
import warnings
import itertools

from ..cqlconn import CqlConn
import gc
import cassandra as cas

import uuid
import bwsample as bws

import logging

# start logger
logger = logging.getLogger(__name__)

# Summary
#   GET     n.a.
#   POST    /bestworst/random/{n_sents}/{m_sets} and params
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


# DELETE
# def extract_spans(ann: dict, keywords: List[str]) -> List[Tuple[int, int]]:
#     out = []
#     if keywords:
#         # add from SPAN given lemma
#         out.extend([e.get('span', None) for e in ann.get('spans', [])
#                     if e.get('lemma', '') in keywords and e.get('span', None)])
#         # add from TOKEN given lemma
#         out.extend([e.get('span', None) for e in ann.get('tokens', [])
#                     if e.get('lemma', '') in keywords and e.get('span', None)])
#         # add from COMPOUND given lemma
#         out.extend(list(itertools.chain(
#             *[e.get('spans', []) for e in ann.get('compounds', [])
#               if e.get('lemma', '') in keywords and e.get('spans', None)])))
#     # done
#     return out


@router.post("/{n_sentences}/{n_examplesets}/{n_top}/{n_offset}")
async def get_bestworst_example_sets(n_sentences: int,
                                     n_examplesets: int,
                                     n_top: int,
                                     n_offset: int,
                                     params: dict):
    """ Query sentence examples with the top N scores (or with offset)
      and sample BWS sets from it.

    Parameters:
    -----------
    n_sentences : int
        The number of sentence examples for each example set

    n_examplesets : int
        The number of example sets

    n_top : int
        Query for sentence examples with the top 1 to N scores

    n_offset : int
        Query for the 1+offset to N+offset scores

    params : dict
        Payload as json. `params['headword'] : str` is expected

    Usage:
    ------
        POST /bestworst/random/{n_sents}/{m_sets} and params

    Examples:
    ---------
        TOKEN="..."
        curl -X POST "http://localhost:55017/v1/bestworst/samples/4/3/100/0" \
            -H  "accept: application/json" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${TOKEN}" \
            -d '{"headword": "Fahrrad"}'

    """
    # read the headword key value
    if params:
        headword = params['headword']
    else:
        return {"status": "failed", "msg": "Please search for a headword."}

    # query database for example items
    try:
        # connect to Cassandra DB
        conn = CqlConn()
        session = conn.get_session()
        # prepare statement to download the whole partion
        stmt = session.prepare(f"""
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
                "context": {"license": row.license, "sentence_id": row.sentence_id},
                "score": row.initial_score,
                "features": {"semantic": row.features1, "syntax": row.features2}
            })
        # clean up
        conn.shutdown()
        del conn, session
    except cas.ReadTimeout as err:
        logger.error(f"Read Timeout problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    except Exception as err:
        logger.error(f"Unknown problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    finally:
        gc.collect()

    # abort if less than `n_sentences`
    if len(items) < n_sentences:
        return {"status": "failed", "msg": "not enough sentences found."}

    # sort by largest score n_top, n_offset
    if len(items) > n_top:
        items = sorted(items, key=lambda x: x["score"], reverse=True)
        items = items[(n_offset):(n_offset + n_top)]

    # Sample overlapping example sets, each shuffled
    # - see https://github.com/satzbeleg/bwsample#sampling
    sampled_sets = bws.sample(
        items, n_items=n_sentences, method='overlap', shuffle=True)

    # Add meta information for the app
    example_sets = []
    for bwset in sampled_sets:
        example_sets.append({
            "set_id": str(uuid.uuid4()),
            "headword": headword,
            "examples": bwset
        })

    return example_sets
