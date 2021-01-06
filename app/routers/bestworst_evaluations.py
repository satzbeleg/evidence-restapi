from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional, Any
# from pydantic import BaseModel

import lorem
import uuid

# Summary
#   GET     /bestworst/{n_sents}/{m_sets}
#               Return M sets of N random sentences
#   POST    n.a.
#   PUT     n.a.
#   DELETE  n.a.
router = APIRouter()


# class ExampleSet(BaseModel):


@router.post("")
async def save_evaluated_examples(data: List[Any]) -> dict:
    stored_setids = []
    for exampleset in data:
        #print(exampleset)
        stored_setids.append(exampleset['set_id'])

    print(stored_setids)
    return {'status': 'success', 'stored-setids': stored_setids}
