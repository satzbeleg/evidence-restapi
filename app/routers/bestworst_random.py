from fastapi import APIRouter, HTTPException
# from typing import List

import lorem
import uuid
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


@router.get("/{n_sentences}")
async def get_bestworst_random_sentence(n_sentences: int):
    """ Create one set of N random sentences (GET)

    Parameters:
    -----------
    n_sentences : int
        The number of sentence examples

    Usage:
    ------
        GET /bestworst/random/{n_sents}
    """
    return [
        {
            "id": str(uuid.uuid4()),
            "text": lorem.sentence()
        }
        for _ in range(n_sentences)
    ]


@router.get("/{n_sentences}/{n_examplesets}")
async def get_bestworst_random_exampleset(n_sentences: int,
                                          n_examplesets: int):
    """ Create M sets of N random sentences (GET)

    Parameters:
    -----------
    n_sentences : int
        The number of sentence examples for each example set

    n_examplesets : int
        The number of example sets

    Usage:
    ------
        GET /bestworst/random/{n_sents}/{m_sets}
    """
    return [{
        "set_id": str(uuid.uuid4()),
        "lemmata": lorem.sentence().split(" ")[0:random.randint(1, 2)],
        "examples": [
            {"id": str(uuid.uuid4()), "text": lorem.sentence()}
            for _ in range(n_sentences)
        ]} for _ in range(n_examplesets)]


@router.post("/{n_sentences}/{n_examplesets}")
async def get_bestworst_random_exampleset2(n_sentences: int,
                                           n_examplesets: int,
                                           params: dict):
    """ Create M sets of N random sentences (POST)

    Parameters:
    -----------
    n_sentences : int
        The number of sentence examples for each example set

    n_examplesets : int
        The number of example sets

    params : dict
        Payload as json. `params['lemmata'] : List[str]` is processed if sent

    Usage:
    ------
        POST /bestworst/random/{n_sents}/{m_sets}
    """
    if params:
        keywords = params['lemmata']
    else:
        keywords = []

    return [{
        "set_id": str(uuid.uuid4()),
        "lemmata": keywords,
        "examples": [
            {"id": str(uuid.uuid4()), "text": lorem.sentence()}
            for _ in range(n_sentences)
        ]} for _ in range(n_examplesets)]
