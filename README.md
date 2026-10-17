# Secure Chat and Network Monitoring Platform

A Python TCP chat application with AES-GCM message encryption, a FastAPI
monitoring API, a TCP availability watcher, and email alerts when the
chat server goes down or recovers.

> **Scope:** This is a security and network-monitoring prototype. It
> does **not** implement Quantum Key Distribution (QKD). It currently
> uses a shared development AES key loaded from an environment variable.
> The `KeyProvider` abstraction is a possible integration point for a
> future QKD key-management system.

## Features

-   TCP chat server and clients using newline-delimited JSON packets.
-   AES-GCM encryption for chat messages.
-   Key-provider abstraction for key retrieval.
-   FastAPI health, metrics, network-check, and port-diagnostic
    endpoints.
-   Periodic TCP availability checks and latency logging.
-   Email alerts when the server transitions to DOWN or recovers to UP.
-   Automated tests for encryption, key-provider behavior, monitoring
    endpoints, watcher transitions, and tampered-message rejection.

## Architecture

``` text
Chat Clients
     |
     | TCP + encrypted JSON packets
     v
Chat Server (server.py) <----- TCP checks ----- Network Watcher (watcher.py)
     |                                              |-- logs/network.log
     |                                              +-- Email alerts
     |
     +---- Runtime metrics
                 ^
                 |
        FastAPI Monitor (monitor.py)
        http://127.0.0.1:8000
```

## Project files

  -----------------------------------------------------------------------
  File                                Purpose
  ----------------------------------- -----------------------------------
  `server.py`                         TCP server, client handling,
                                      message validation, runtime metrics

  `client.py`                         Chat client, encryption, and
                                      message display

  `security.py`                       AES-GCM encryption and decryption

  `key_provider.py`                   Development key provider
                                      abstraction

  `monitor.py`                        FastAPI monitoring endpoints

  `watcher.py`                        TCP checks, logging, and email
                                      alerts

  `test_security.py`                  Encryption and tampering tests

  `test_key_provider.py`              Key-provider tests

  `test_server_security.py`           Server rejection test for tampered
                                      messages

  `test_monitor.py`                   Monitoring API tests

  `test_watcher.py`                   Watcher and alert-transition tests

  `requirements.txt`                  Python dependencies
  -----------------------------------------------------------------------

## Requirements

-   Python 3
-   `pip`
-   Gmail SMTP app password if testing email alerts

## Setup

### 1. Clone the repository

``` bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd ChatRoom
```

Replace the placeholder with your repository URL.

### 2. Create and activate a virtual environment

``` bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

``` bash
python3 -m pip install -r requirements.txt
```

### 4. Configure `.env`

Create a `.env` file in the project root. Do not commit it.

``` dotenv
CHAT_DEV_KEY=REPLACE_WITH_64_HEX_CHARACTERS
MONITOR_EMAIL=your_sender_email@gmail.com
MONITOR_EMAIL_APP_PASSWORD=your_gmail_app_password
ALERT_EMAIL=your_recipient_email@example.com
```

Generate a 32-byte development key (64 hexadecimal characters):

``` bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Put the generated value in `CHAT_DEV_KEY`. For Gmail SMTP, use an app
password where required, not your normal account password. The watcher
requires valid email settings in the current configuration.

## Run the application

Use separate terminal windows and activate the virtual environment in
each one.

### Terminal 1: chat server

``` bash
source venv/bin/activate
python3 server.py
```

Default TCP address: `127.0.0.1:55556`.

### Terminal 2: monitoring API

``` bash
source venv/bin/activate
uvicorn monitor:app --host 127.0.0.1 --port 8000
```

Interactive API docs: <http://127.0.0.1:8000/docs>.

### Terminal 3: network watcher

``` bash
source venv/bin/activate
python3 watcher.py
```

The watcher checks connectivity periodically, writes to
`logs/network.log`, and emails alerts on DOWN and recovery transitions.

### Terminal 4 and beyond: chat clients

``` bash
source venv/bin/activate
python3 client.py
```

Run this command in multiple terminals to test chatting between clients.

## Monitoring API

The API defaults to `127.0.0.1:8000`.

  -----------------------------------------------------------------------
  Endpoint                            Description
  ----------------------------------- -----------------------------------
  `GET /health`                       Reports server status and uptime

  `GET /metrics`                      Returns connection, message,
                                      disconnect, and send-error
                                      counters, active clients, and
                                      uptime

  `GET /network-check`                Checks TCP reachability and reports
                                      latency

  `GET /diagnostics/ports`            Checks selected local TCP ports
  -----------------------------------------------------------------------

Try the endpoints:

``` bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/metrics
curl http://127.0.0.1:8000/network-check
curl http://127.0.0.1:8000/diagnostics/ports
```

These endpoints are intended for local development. Do not expose the
monitoring API publicly without authentication and appropriate access
controls.

## Run tests

With the virtual environment activated, from the project root:

``` bash
python3 -m pytest -v
```

The current test suite has **16 passing tests** covering security
helpers, key-provider behavior, monitoring endpoints, watcher
transitions, and server rejection of tampered ciphertext.

## Security notes and limitations

-   **No QKD implementation:** this project does not include quantum
    hardware, a quantum channel, a QKD protocol, or a QKD key-management
    service.
-   **Development key:** the server and clients use a shared AES key
    loaded from `.env`. This is for a local prototype, not production
    key management.
-   **Not end-to-end encrypted:** the server decrypts messages to
    validate them before forwarding the encrypted packet, so the server
    process can access plaintext.
-   **No user authentication:** nicknames do not prove identity; there
    is no account or authorization system.
-   **Local-only defaults:** the server and monitoring API bind to
    loopback by default. Changing bind addresses can expose them to
    other machines.
-   **Monitoring access:** monitoring endpoints do not implement
    authentication.
-   **Operational hardening:** email retry logic, persistent metrics
    storage, rate limiting, and production deployment controls are not
    implemented.

AES-GCM requires a unique nonce for each encryption under the same key.
Never reuse a nonce with the same AES-GCM key.

## Possible future work

-   Connect `KeyProvider` to a real QKD key-management system, if one is
    available.
-   Add authenticated client identities and access control.
-   Add retry/backoff handling for failed email alerts.
-   Persist metrics and provide historical reporting.
-   Add deployment hardening and configurable network binding.

## Project summary

This project demonstrates Python socket programming, AES-GCM
authenticated encryption, environment-based configuration, automated
testing, FastAPI monitoring, TCP availability checks, runtime metrics,
logging, and SMTP alerting.
