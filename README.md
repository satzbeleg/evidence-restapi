# EVIDENCE Projekt: REST API zwischen Postgres DB und Vue Web App

## Locale Installation im einer virtuellen Python Umgebung
(0) Installiere Ubuntu/Debian Pakete

```bash
sudo apt update
sudo apt install -y --no-install-recommends build-essential python3-dev python3-venv
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

```
export EV_PSQL_HOST=localhost
export EV_PSQL_PORT=55015
export EV_PSQL_USERNAME=postgres
export EV_PSQL_PASSWORD=password1234
```

(3) Starte den FastAPI Server

```bash
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 55017 --reload --log-level debug
```

(4) Authentifiziere Dich mit dem Testkonto. Fordere einen Access Token an.

```bash
curl -X POST "http://0.0.0.0:55017/v1/auth/login" \
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

