# EVIDENCE Project: REST API for UI

## Local installation in a virtual env
(0) Install OS requirements

```bash
sudo apt update
sudo apt install -y --no-install-recommends build-essential python3-dev python3-venv
```

(1) Run install script

```bash
bash install.sh
```

(2) Start Server

```
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 55017 --reload --log-level debug
```

(3) Run some requests

```
curl http://127.0.0.1:55017/bestworst/4
curl -I --http2 http://127.0.0.1:55017
```

```python
import requests
data = {"username": "johndoe", "password": "secret"}
resp = requests.post("http://localhost:55017/v1/token", data)
print(resp.text)
```

## Run as docker container
Call Docker Compose

```
docker network create --driver bridge \
    --subnet=172.20.253.0/28 \
    --ip-range=172.20.253.8/29 \
    evidence-backend-network

docker-compose up --build
```

(Start docker daemon before, e.g. `open /Applications/Docker.app` on MacOS).

Check

```
curl http://localhost:55017
```

Notes: Only `main.py` is used in `Dockerfile`.


## Misc Commands
- Check pip8 syntax: `flake8 --ignore=F401 --exclude=$(grep -v '^#' .gitignore | xargs | sed -e 's/ /,/g')`
- Show the docs `http://localhost:55017/docs`
- Show Redoc: `http://localhost:55017/redoc`
