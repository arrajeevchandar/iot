#pragma once
// Copy to secrets.h. Never commit credentials. Wokwi's simulated Wi-Fi is open.
#define WIFI_SSID "Wokwi-GUEST"
#define WIFI_PASSWORD ""
// Public HTTPS server reachable from Wokwi, without a trailing slash.
#define CLOUD_URL ""
#define DEVICE_ID "classroom-101"
#define DEVICE_TOKEN ""
// PEM root CA for your HTTPS endpoint. TLS verification is mandatory.
#define CLOUD_ROOT_CA ""
// Plain HTTP is permitted only when explicitly enabled for a local lab capture.
#define ALLOW_INSECURE_HTTP false
