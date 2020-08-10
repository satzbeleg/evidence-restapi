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
uvicorn app.main:app --reload
```

(3) Run some requests

```
curl http://127.0.0.1:8000/items/5?q=somequery
```

## Run as docker container
Call Docker Compose

```
sudo docker-compose up
```

(Start docker daemon before, e.g. `open /Applications/Docker.app` on MacOS).

Check

```
curl http://localhost:12345
```

Notes: Only `main.py` is used in `Dockerfile`.


## Misc Commands
- Check pip8 syntax: `flake8 --ignore=F401 --exclude=$(grep -v '^#' .gitignore | xargs | sed -e 's/ /,/g')`
- Show the docs `http://localhost:12345/docs`
- Show Redoc: `http://localhost:12345/redoc`
