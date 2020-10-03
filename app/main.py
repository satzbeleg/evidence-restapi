from fastapi import FastAPI
import lorem
import time
import random

# define the server url (excl. hostname:port)
# srvurl = "/testapi/v1"
srvurl = "/v1"

# basic information
app = FastAPI(
    title="EVIDENCE Project: REST API for UI",
    descriptions=(
        "The purpose of this REST API is to connect the a) UI "
        "with b) the PostgreSQL database, and return good examples "
        "with respect to c) the latest PyTorch model."),
    version="0.1.0",
    openapi_url=f"{srvurl}/openapi.json",
    docs_url=f"{srvurl}/docs",
    redoc_url=f"{srvurl}/redoc"
)


def my_rand_id():
    part1 = int(time.time()) % 100000
    part2 = random.randint(1000, 9999)
    return int(f"{part1}{part2}")


# specify the endpoints
@app.get(f"{srvurl}/")
def read_root():
    return {"msg": "Welcome to the EVIDENCE project."}


# retrieve random examples for bestworst
# example: http://127.0.0.1:8000/bestworst/random/4
@app.get(srvurl + "/bestworst/random/{n_sentences}")
async def get_bestworst_random_sentence(n_sentences: int):
    return [
        {
            "id": my_rand_id(),
            "text": lorem.sentence()
        }
        for _ in range(n_sentences)
    ]


@app.get(srvurl + "/bestworst/random/{n_sentences}/{n_examplesets}")
async def get_bestworst_random_exampleset(n_sentences: int,
                                          n_examplesets: int):
    return [{
            "set_id": f"demo-exampleset-{my_rand_id()}",
            "examples": [
                {"id": my_rand_id(), "text": lorem.sentence()}
                for _ in range(n_sentences)
            ]} for _ in range(n_examplesets)]
