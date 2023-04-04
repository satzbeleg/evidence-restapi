from fastapi import APIRouter
from ..cqlconn import CqlConn
import cassandra as cas
import gc
import logging
import numpy as np
from ..transform import i2f

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
    headword = params.get('headword')
    if headword is None:
        return {"status": "failed", "num": 0,
                "msg": f"No headword='{headword}' provided"}

    # query database for example items
    try:
        # prepare statement to download the whole partion
        stmt = cas.query.SimpleStatement(f"""
            SELECT headword, example_id, sentence, sent_id
                 , spans, annot, biblio, license, score
                 , feats1
                 , feats2, feats3, feats4, feats5
                 , feats6, feats7, feats8, feats9
                 , feats12, feats13, feats14
            FROM {session.keyspace}.tbl_features
            WHERE headword='{headword}';
            """, fetch_size=5000)

        # fetch partition
        dat = session.execute(stmt)
        # read data to list of json
        items = []
        feats = [[] for i in range(12)]
        for row in dat:
            feats[0].append(row.feats1)
            feats[1].append(row.feats2)
            feats[2].append(row.feats3)
            feats[3].append(row.feats4)
            feats[4].append(row.feats5)
            feats[5].append(row.feats6)
            feats[6].append(row.feats7)
            feats[7].append(row.feats8)
            feats[8].append(row.feats9)
            feats[9].append(row.feats12)
            feats[10].append(row.feats13)
            feats[11].append(row.feats14)
            items.append({
                "example_id": str(row.example_id),
                "text": row.sentence,
                "headword": row.headword,
                "spans": row.spans,
                "context": {
                    "license": row.license,
                    "biblio": row.biblio,
                    "sentence_id": str(row.sent_id)},
                "score": row.score
            })
        feats = i2f(*feats)
        feats = feats.tolist()
        for i, feat in enumerate(feats):
            items[i]["features"] = feat

    except cas.ReadTimeout as err:
        logger.error(f"Read Timeout problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    except Exception as err:
        logger.error(f"Unknown problems with '{headword}': {err}")
        return {"status": "failed", "msg": err}
    finally:
        gc.collect()

    # sort by largest score n_top, n_offset
    if len(items) > n_examples:
        items = sorted(items, key=lambda x: x["score"], reverse=True)
        if (len(items) > n_offset) and (n_offset > 0):
            items = items[n_offset:]
        if len(items) > n_top:
            items = items[:n_top]

    # abort if no query results
    if len(items) == 0:
        return {"status": "failed", "msg": "no sentences found."}

    # randomly sample items
    return np.random.choice(
        items, min(len(items), n_examples),
        replace=False).tolist()
