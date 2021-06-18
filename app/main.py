from fastapi import FastAPI, Depends

from fastapi.middleware.cors import CORSMiddleware
from .config import config_web_app

from .routers import (
    auth_legacy, auth_email, user_settings,
    bestworst_random, bestworst_samples, bestworst_evaluations
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

# allow exceptions to develop on the same machine/host (i.e. localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(set([
        "http://localhost:8080",
        f"http://localhost:{config_web_app.get('port')}",
        "http://127.0.0.1:8080",
        f"http://127.0.0.1:{config_web_app.get('port')}",
        "http://0.0.0.0:8080",
        f"http://0.0.0.0:{config_web_app.get('port')}",
        f"https://{config_web_app.get('host')}:{config_web_app.get('port')}"
    ])),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# specify the endpoints
@app.get(f"/{version}/")
def read_root():
    return {"msg": "Welcome to the EVIDENCE project."}


app.include_router(
    auth_legacy.router,
    prefix=f"/{version}/auth-legacy",
    tags=["auth"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

app.include_router(
    auth_email.router,
    prefix=f"/{version}/auth",
    tags=["auth"],
    # dependencies=[Depends(get_token_header)],
    # responses={404: {"description": "Not found"}},
)

# POST /user/settings
app.include_router(
    user_settings.router,
    prefix=f"/{version}/user/settings",
    tags=["user"],
    dependencies=[Depends(auth_legacy.get_current_user)],
    # responses={404: {"description": "Not found"}},
)


# GET /bestworst/random/{n_sents}
# GET /bestworst/random/{n_sents}/{m_sets}
app.include_router(
    bestworst_random.router,
    prefix=f"/{version}/bestworst/random",
    tags=["bestworst"],
    dependencies=[Depends(auth_legacy.get_current_user)],
    # responses={404: {"description": "Not found"}},
)

# POST /bestworst/random/{n_sents}/{m_sets} and params
app.include_router(
    bestworst_samples.router,
    prefix=f"/{version}/bestworst/samples",
    tags=["bestworst"],
    dependencies=[Depends(auth_legacy.get_current_user)],
    # responses={404: {"description": "Not found"}},
)


# POST /bestworst/evaluations
app.include_router(
    bestworst_evaluations.router,
    prefix=f"/{version}/bestworst/evaluations",
    tags=["bestworst"],
    dependencies=[Depends(auth_legacy.get_current_user)],
    # responses={404: {"description": "Not found"}},
)
