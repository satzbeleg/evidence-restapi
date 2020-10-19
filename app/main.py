from fastapi import FastAPI

from .routers import (
    bestworst_random, token
)


# API version
version = "v1"

# basic information
app = FastAPI(
    title="EVIDENCE Project: REST API for UI",
    descriptions=(
        "The purpose of this REST API is to connect the a) UI "
        "with b) the PostgreSQL database, and return good examples "
        "with respect to c) the latest PyTorch model."),
    version="0.1.0",
    openapi_url=f"/{version}/openapi.json",
    docs_url=f"/{version}/docs",
    redoc_url=f"/{version}/redoc"
)


# specify the endpoints
@app.get(f"/{version}/")
def read_root():
    return {"msg": "Welcome to the EVIDENCE project."}


app.include_router(
    token.router,
    prefix=f"/{version}/token",
    tags=["auth", "token"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)


# GET /bestworst/random/{n_sents}
# GET /bestworst/random/{n_sents}/{m_sets}
app.include_router(
    bestworst_random.router,
    prefix=f"/{version}/bestworst/random",
    tags=["sentences"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)
