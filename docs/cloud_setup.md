# Free dashboard and remote connectivity

## No-account local mode

`bash scripts/run.sh` starts a loopback-only service on port 8000 with an interactive software classroom. There is no account creation or cloud subscription. This is a complete local software demo but is not an ESP32 network simulation. A Wokwi public gateway cannot connect to the host's loopback service.

## Public HTTPS deployment

Use an existing server with HTTPS, or a free Python/container hosting tier that permits inbound HTTPS and outbound replies. Provider quotas and pricing can change; do not enable a paid plan merely for this project. Free ephemeral containers may discard SQLite data on restart. A free tunnel can also expose the local service, but the tunnel endpoint must support machine clients without a browser login/interstitial. Availability of a third-party host is not guaranteed by this repository.

1. Run `python scripts/create_credentials.py` locally. It creates `.env` with distinct random dashboard and device tokens, only if the file does not already exist.
2. Privately transfer those values into the hosting service's secret/environment settings: `DASHBOARD_TOKEN`, `DEVICE_TOKEN`, `PUBLIC_DEPLOYMENT=1`, and optionally `SIMULATOR_ENABLED=0` to hide the local software device. Do not paste tokens into chat, commit them, or put them in URLs.
3. Install `requirements.txt`; launch `python -m uvicorn dashboard.app:app --host 0.0.0.0 --port 8000` with one worker. The included Dockerfile performs the same setup and requires tokens via environment variables. Map the host's required port if different.
4. Route a public HTTPS hostname to that port. Configure the hosting health check at `/api/health`. Set a body-size limit and rate limit at the reverse proxy for an Internet deployment. Use persistent storage for `runtime/` if history must survive redeploys.
5. Verify the health response and load the dashboard. Select **Configure access token** and enter only the application dashboard token. It is retained in that tab's session storage. The server rejects unauthenticated data/control calls.
6. Copy `firmware/include/secrets.example.h` to the ignored `secrets.h`. Set `CLOUD_URL` to the HTTPS origin, `DEVICE_ID` to a unique room, `DEVICE_TOKEN` to the device token, and `CLOUD_ROOT_CA` to the PEM root certificate for that endpoint. Use a C++ raw string for multiline PEM. Obtain the root certificate from your certificate authority's official distribution, not an unverified download. Keep `ALLOW_INSECURE_HTTP` false.
7. Rebuild firmware and upload the merged binary in Wokwi. Wait for Wi-Fi and NTP, then watch for the room in the dashboard. TLS cannot connect without a valid clock/root CA; serial logs indicate a configuration error or HTTP status without printing the token.
8. Send a MANUAL command. It must become acknowledged in telemetry, and Wokwi's actual LED/servo must change. Stop the simulation and confirm the UI marks it offline. Restart it to validate reconnection.

The app validates token requirements in public mode and denies non-loopback access when credentials are unset. A public deployment should also have HTTPS, request limits, and suitably disposable academic data. Wokwi's public gateway is monitored by its operator; do not send sensitive real-world data.

## API contract

| Route | Authentication | Purpose |
|---|---|---|
| `GET /api/health` | None | Basic status |
| `GET /api/rooms` | Dashboard token | Latest state, online flag, desired command |
| `GET /api/rooms/{id}/history` | Dashboard token | Up to 120 snapshots |
| `POST /api/rooms/{id}/commands` | Dashboard token | Complete mode/light/fan/servo desired state |
| `POST /api/rooms/{id}/sensors` | Dashboard token | Local simulator only |
| `POST /api/devices/{id}/telemetry` | Device token | Device state upload and command response |

Protected calls use the `Authorization: Bearer …` header. No tokens belong in query strings. Sensor and actuator bounds are validated; NaN/infinity, unknown fields, invalid modes, and out-of-range angles are rejected. Device and dashboard tokens are not interchangeable.
