from fastapi import APIRouter, HTTPException
from typing import List, Tuple
import warnings
import itertools

import psycopg2
from ..config import config_ev_psql
import gc

import random
import uuid

# Summary
#   GET     n.a.
#   POST    /bestworst/random/{n_sents}/{m_sets} and params
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


def get_sentence_text(sent_ids: List[str]) -> dict:
    """Download raw sentence text from SentenceStore API

    Parameters:
    -----------
    sent_ids : List[str]
        A list of UUID4 sentence_id that are compatible to the
          SentenceStore API.

    Return:
    -------
    dict
        A JSON object with sentence_id as key, and sentence_text as value.

    Examples:
    ---------
        dbsentences = get_sentence_text([
            '37e76b95-1106-4818-8486-2985807db988',
            '8dde3a62-9f50-432d-8d4e-886e0f9c032f'])
    """
    warnings.warn((
        "The `evidence.sentences_cache` table is used temporarily. "
        "The plan is use the SentenceStore API lateron!"), FutureWarning)

    # this will be replaced by an REST API call to the SentenceStore lateron
    try:
        # connect to DB
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()
        # query
        cur.execute('''
            SELECT sentence_id, sentence_text, annotation
            FROM evidence.sentences_cache
            WHERE sentence_id::text LIKE ANY(%s::text[]);
            ''', [sent_ids])
        dbsentences = {key: {"text": txt, "annotation": ann}
                       for key, txt, ann in cur.fetchall()}
        conn.commit()
        # clean up
        cur.close()
        conn.close()
        del cur, conn
    except Exception as err:
        print(err)
        return {}
    finally:
        gc.collect()
        return dbsentences


def extract_spans(ann: dict, keywords: List[str]) -> List[Tuple[int, int]]:
    out = []
    if keywords:
        # add from SPAN given lemma
        out.extend([e.get('span', None) for e in ann.get('spans', [])
                    if e.get('lemma', '') in keywords and e.get('span', None)])
        # add from TOKEN given lemma
        out.extend([e.get('span', None) for e in ann.get('token', [])
                    if e.get('lemma', '') in keywords and e.get('span', None)])
        # add from COMPOUND given lemma
        out.extend(list(itertools.chain(
            *[e.get('spans', []) for e in ann.get('compound', [])
              if e.get('lemma', '') in keywords and e.get('spans', None)])))
    # done
    return out


# POST /bestworst/random/{n_sents}/{m_sets} and params
@router.post("/{n_sentences}/{n_examplesets}/{n_top}/{n_offset}")
async def get_bestworst_example_sets(n_sentences: int,
                                     n_examplesets: int,
                                     n_top: int,
                                     n_offset: int,
                                     params: dict):
    """

    Examples:
    ---------
        TOKEN="..."
        curl -X POST "http://localhost:55017/v1/bestworst/samples/4/3/100/0" \
            -H  "accept: application/json" \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer ${TOKEN}" \
            -d '{"lemmata": ["impeachment"]}'

    """
    # read the lemmata key value
    if params:
        keywords = params['lemmata']
    else:
        return {"status": "failed", "msg": "Please search for a lemma."}

    # query database for example items
    try:
        # Open connection to EVIDENCE database
        conn = psycopg2.connect(**config_ev_psql)
        cur = conn.cursor()
        # generate query string and run query
        n_examples = (n_examplesets + 1) * max(1, n_sentences - 1)
        cur.execute((
            "SELECT sentence_id, context, score "
            "FROM evidence.query_by_lemmata(%s::text[], %s::int, %s::int) "
            "ORDER BY random() LIMIT %s;"),
            [keywords, n_top, n_offset, n_examples])
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

    # abort if less than `n_sentences`
    if len(items) < n_sentences:
        return {"status": "failed", "msg": "not enough sentences found."}

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
        text = f"SentenceID '{row[0]}' doesn't exist in the SentenceStore API."
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
            "score": row[2]
        })

    # split into overlapping example sets
    example_sets = []
    for s in range(0, len(items2), max(1, n_sentences - 1)):
        example_sets.append({
            "set_id": str(uuid.uuid4()),
            "lemmata": keywords,
            "examples": items2[s:(s + n_sentences)]
        })

    # draw 1-2 missing example items from other sets
    n_missing = max(n_sentences - len(example_sets[-1]['examples']), 0)
    for i in range(n_missing):
        n = min(len(example_sets[i]['examples']), n_sentences)
        j = random.randint(0, n - 1)
        selected = example_sets[i]['examples'][j]
        example_sets[-1]['examples'].append(selected)

    # shuffle the examples
    for i in range(len(example_sets)):
        random.shuffle(example_sets[i]['examples'])

    return example_sets
