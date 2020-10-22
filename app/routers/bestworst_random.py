from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

import lorem
import time
import random

# Summary
#   GET     /bestworst/random/{n_sents}
#               Return one set of N random sentences
#   GET     /bestworst/random/{n_sents}/{m_sets}
#               Return M sets of N random sentences
#   POST    n.a.
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


# utility function
def my_rand_id():
    part1 = int(time.time()) % 100000
    part2 = random.randint(1000, 9999)
    return int(f"{part1}{part2}")


# GET /bestworst/random/{n_sents}
# Return one set of N random sentences
@router.get("/{n_sentences}")
async def get_bestworst_random_sentence(n_sentences: int):
    return [
        {
            "id": my_rand_id(),
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
            "set_id": f"demo-exampleset-{my_rand_id()}",
            "examples": [
                {"id": my_rand_id(), "text": lorem.sentence()}
                for _ in range(n_sentences)
            ]} for _ in range(n_examplesets)]
