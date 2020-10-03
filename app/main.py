from fastapi import FastAPI

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


# specify the endpoints
@app.get(f"{srvurl}/")
def read_root():
    return {"msg": "Hello World"}


@app.get(f"{srvurl}/items/")
async def read_items_null():
    return {"item_id": None}


@app.get(srvurl + "/items/{item_id}")
async def read_items(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
