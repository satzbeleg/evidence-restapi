# REST API (fastapi) Postgres DB und Vue Web App

## Lokale Installation im einer virtuellen Python Umgebung
(0) Installiere Ubuntu/Debian Pakete

```bash
sudo apt update
sudo apt install -y --no-install-recommends build-essential python3-dev python3-venv
sudo apt install -y --no-install-recommends libpq-dev
```

(1) Installiere FastAPI in der eigenen virtuellen Umgebung

```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install --upgrade pip
pip3 install -r requirements-server.txt
pip3 install -r requirements-dev.txt
pip3 install -r requirements.txt
```

(2) Konfiguriere Postgres Variablen

Für den Fall, dass die Postgres Datenbank auf demselben Host läuft (Und nicht via docker network)

```bash
export REST_DBAUTH_HOST=localhost
export REST_DBAUTH_PORT=55014
export REST_DBAUTH_USER=postgres
export REST_DBAUTH_PASSWORD=password1234

export REST_DBAPPL_HOST=localhost
export REST_DBAPPL_PORT=55015
export REST_DBAPPL_USER=postgres
export REST_DBAPPL_PASSWORD=password1234

export CORS_WEBAPP_HOSTPORT=55018
export CORS_WEBAPP_EXTERNAL_URL=localhost
```

(3) Starte den FastAPI Server

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 55017 --reload --log-level debug
```

(4) Authentifiziere Dich mit dem Testkonto. Fordere einen Access Token an.

```bash
curl -X POST "http://0.0.0.0:55017/v1/auth-legacy/login" \
    -H "accept: application/json" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=testuser2&password=secret2" \
    > mytokendata
TOKEN=$(cat mytokendata | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

(5) Probiere andere Requests aus

```bash
curl -X GET "http://127.0.0.1:55017/v1/bestworst/random/4" \
    -H "accept: application/json" \
    -H "Authorization: Bearer ${TOKEN}"
```

```bash
curl -X POST "http://localhost:55017/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" -d '{"hello":"world3"}'

curl -X GET "http://localhost:55017/v1/user/settings" \
    -H  "accept: application/json" -H  "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}"
```

## Authentifizierung in Python

```python
import requests
data = {"username": "testuser1", "password": "secret"}
resp = requests.post("http://localhost:55017/v1/auth/login", data)
print(resp.text)

TOKEN = resp.json()['access_token']
headers = {'Authorization': f"Bearer {TOKEN}"}

resp = requests.get("http://localhost:55017/v1/bestworst/random/5", headers=headers)
print(resp.json())
```



## Benutzerkonten manuell erstellen (Zwischenlösung)
Starte die virtuelle python Umgebung und starte die Console

```bash
source .venv/bin/activate
python3
```

Hashe das Password

```python
password = "supergeheim"

from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["sha512_crypt"], deprecated="auto") 
hashed = pwd_context.hash(password)
print(hashed)
```

Öffne die PSQL Console (siehe []())

```bash
psql --host=127.0.0.1 --port=55015 --username=postgres
```

Füge neuen User ein

```sql
SELECT auth.add_new_user_with_localpw('benutzer789', '$6$rounds=656000$PSAR1THK2sFnMpoJ$iFk/ia.wcLWeWBOmcCG7TRjG0HUpnUuWZzcxRpiRhgdphmXQscUtjmvFf9xuBxMdG25Wef1CSacKZdetY7CBj1');
```



## Run REST API in a docker container
The file `docker-compose.yml` contains an **configuration example** how to deploy the REST API as docker container. It is recommended to add this repository as git submodule to an deployment repository with a central Docker Compose configuration that suits your needs. 

```sh
# Host Server's Port Settings
export RESTAPI_HOSTPORT=55017

# Postgres Settings
# WARNING: You need to start the database container first
export DBAPPL_PASSWORD=password1234
export DBAUTH_PASSWORD=password1234

# REST API Settings
export RESTAPI_NUM_WORKERS=1
export RESTAPI_SECRET_KEY=$(openssl rand -hex 32)
export RESTAPI_TOKEN_EXPIRY=1440  # in minutes

# WEB APP Settings
export WEBAPP_HOSTPORT=55018
export WEBAPP_EXTERNAL_URL=localhost
#export WEBAPP_EXTERNAL_URL=evidence.bbaw.de

docker compose -p evidence -f network.yml -f restapi.yml up --build
```

(Start docker daemon before, e.g. `open /Applications/Docker.app` on MacOS).

Check

```
curl http://localhost:55017/v1/
```

Notes: Only `main.py` is used in `Dockerfile`.


## Misc Commands
- Check pip8 syntax: `flake8 --ignore=F401 --exclude=$(grep -v '^#' .gitignore | xargs | sed -e 's/ /,/g')`
- Run unit tests: `pytest`
- Show the docs `http://localhost:55017/docs`
- Show Redoc: `http://localhost:55017/redoc`



Clean Up code

```bash
# delete  `.pyc` files: 
find . -type f -name "*.pyc" | xargs rm

# delete `__pycache__` folders 
find . -type d -name "__pycache__" | xargs rm -r

# delete `.pytest_cache` folder
rm -r .pytest_cache

# delete virtual env
rm -r .venv
```

