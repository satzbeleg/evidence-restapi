from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import lorem
import uuid

# Summary
#   GET     /bestworst/random/{n_sents}
#               Return one set of N random sentences
#   GET     /bestworst/random/{n_sents}/{m_sets}
#               Return M sets of N random sentences
#   POST    n.a.
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


# GET /bestworst/random/{n_sents}
# Return one set of N random sentences
@router.get("/{n_sentences}")
async def get_bestworst_random_sentence(n_sentences: int):
    return [
        {
            "id": str(uuid.uuid4()),
            "text": lorem.sentence()
        }
        for _ in range(n_sentences)
    ]


# GET /bestworst/random/{n_sents}/{m_sets}
# return M sets of N random sentences
@router.get("/{n_sentences}/{n_examplesets}")
async def get_bestworst_random_exampleset(n_sentences: int,
                                          n_examplesets: int):
    return [{
            "set_id": str(uuid.uuid4()),
            "examples": [
                {"id": str(uuid.uuid4()), "text": lorem.sentence()}
                for _ in range(n_sentences)
            ]} for _ in range(n_examplesets)]
