from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from .auth_email import get_current_user

from ..cqlconn import CqlConn
import cassandra as cas
import cassandra.query
import uuid
import gc
import json
import numpy as np
import numba

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


@numba.njit
def compute_simi_matrix(x):
    n = x.shape[0]
    y = np.diag(np.ones(n, dtype=np.float32))
    for i in range(n):
        for j in range(i + 1, n):
            y[i, j] = np.mean(x[i] == x[j])
            y[j, i] = y[i, j]
    return y


# https://github.com/satzbeleg/keras-hrp/blob/main/keras_hrp/serialize.py#L11
def int8_to_bool(serialized: List[np.int8]) -> List[bool]:
    return np.unpackbits(
        serialized.astype(np.uint8),
        bitorder='big').reshape(-1)


@router.post("")
async def create_similarity_matrices(data: Dict[str, Any],
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
    curl -X POST "http://localhost:55017/v1/variation/similarity-matrices" \
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
    limit = data.get("limit", 30)

    # download data
    try:
        # prepare statement
        stmt = cas.query.SimpleStatement(f"""
            SELECT sentence, biblio, score,
                feats1, hashes15, hashes16, hashes18
            FROM {session.keyspace}.tbl_features
            WHERE headword='{headword}';
            """, fetch_size=5000)
        # read fetched rows
        sentences = []
        biblio = []
        scores = []
        feats_semantic = []
        hashes_grammar = []
        hashes_duplicate = []
        hashes_biblio = []
        for row in session.execute(stmt):
            sentences.append(row.sentence)
            biblio.append(row.biblio)
            scores.append(row.score)
            feats_semantic.append(row.feats1)
            hashes_grammar.append(row.hashes15)
            hashes_duplicate.append(row.hashes16)
            hashes_biblio.append(row.hashes18)
        # delete
        del stmt
        gc.collect()
    except Exception as err:
        print(err)
        gc.collect()
        return {"status": "failed", "num": 0, "error": err,
                "msg": "Unknown error"}

    if len(sentences) == 0:
        return {"status": "failed", "num": 0,
                "msg": "No sentence examples"}

    # convert and enforce data type
    sentences = np.array(sentences)
    biblio = np.array(biblio)
    scores = np.array(scores)
    feats_semantic = np.vstack(
        [int8_to_bool(np.array(enc)) for enc in feats_semantic])
    hashes_grammar = np.array(hashes_grammar, dtype=np.int32)
    hashes_duplicate = np.array(hashes_duplicate, dtype=np.int32)
    hashes_biblio = np.array(hashes_biblio, dtype=np.int32)

    # chop the smallest scores
    idx = np.flip(np.argsort(scores))
    idx = idx[:limit]
    sentences = sentences[idx]
    biblio = biblio[idx]
    scores = scores[idx]
    feats_semantic = feats_semantic[idx]
    hashes_grammar = hashes_grammar[idx]
    hashes_duplicate = hashes_duplicate[idx]
    hashes_biblio = hashes_biblio[idx]

    # Compute Similarity matrices
    mat_semantic = compute_simi_matrix(feats_semantic)
    mat_grammar = compute_simi_matrix(hashes_grammar)
    mat_duplicate = compute_simi_matrix(hashes_duplicate)
    mat_biblio = compute_simi_matrix(hashes_biblio)

    # done
    results = {
        'status': 'success',
        'num': idx.shape[0],
        'sentences': sentences.tolist(),
        'biblio': biblio.tolist(),
        'scores': scores.tolist(),
        'simi-semantic': mat_semantic.tolist(),
        'simi-grammar': mat_grammar.tolist(),
        'simi-duplicate': mat_duplicate.tolist(),
        'simi-biblio': mat_biblio.tolist()
    }
    return results
