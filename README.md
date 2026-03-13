# LAN File Server

Flask + SQLite LAN file sharing starter.

## Run

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Default startup uses HTTPS with a self-signed dev certificate on port `8443`.

Open `https://127.0.0.1:8443`.

## Runtime options

Use your own certificate:

```bash
SSL_CERT_FILE=/path/to/cert.pem SSL_KEY_FILE=/path/to/key.pem PORT=8443 python app.py
```

Temporarily run HTTP only:

```bash
ENABLE_HTTPS=0 PORT=5001 python app.py
```
