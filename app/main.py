from fastapi import FastAPI, Depends

from fastapi.middleware.cors import CORSMiddleware
from .config import config_web_app

from .routers import (
    auth_email,
    user_settings,
    bestworst_random,
    bestworst_samples,
    bestworst_evaluations,
    interactivity_deleted_episodes,
    interactivity_training_examples,
    similarity_matrices
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

# allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# specify the endpoints
@app.get(f"/{version}/")
def read_root():
    return {"msg": "Welcome to the EVIDENCE project."}


app.include_router(
    auth_email.router,
    prefix=f"/{version}/auth",
    tags=["auth"],
    # dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

# POST /user/settings
app.include_router(
    user_settings.router,
    prefix=f"/{version}/user/settings",
    tags=["user"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)


# GET /bestworst/random/{n_sents}
# GET /bestworst/random/{n_sents}/{m_sets}
app.include_router(
    bestworst_random.router,
    prefix=f"/{version}/bestworst/random",
    tags=["bestworst"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)

# POST /bestworst/random/{n_sents}/{m_sets} and params
app.include_router(
    bestworst_samples.router,
    prefix=f"/{version}/bestworst/samples",
    tags=["bestworst"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)


# POST /bestworst/evaluations
app.include_router(
    bestworst_evaluations.router,
    prefix=f"/{version}/bestworst/evaluations",
    tags=["bestworst"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)


# POST /interactivity/deleted
app.include_router(
    interactivity_deleted_episodes.router,
    prefix=f"/{version}/interactivity/deleted-episodes",
    tags=["interactivity"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)

# POST /interactivity/examples
app.include_router(
    interactivity_training_examples.router,
    prefix=f"/{version}/interactivity/training-examples",
    tags=["interactivity"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)

# POST /similarity
app.include_router(
    similarity_matrices.router,
    prefix=f"/{version}/variation/similarity-matrices",
    tags=["variation"],
    dependencies=[Depends(auth_email.get_current_user)],
    responses={404: {"description": "Not found"}},
)
