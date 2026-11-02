# Analyze actual IoT traffic with Wireshark

## Wokwi network capture

Wokwi's [official Wi-Fi guide](https://docs.wokwi.com/guides/esp32-wifi#viewing-wifi-traffic-with-wireshark) documents a PCAP download in the browser simulator:

1. Run the ESP32 circuit and allow it to connect to `Wokwi-GUEST`.
2. Configure a real public HTTPS dashboard to observe telemetry; without a URL you will see Wi-Fi/DHCP/NTP activity, not successful telemetry HTTP exchanges.
3. Run for 30–60 simulated seconds, change sensors, and issue a MANUAL command from the dashboard.
4. Click the simulator's Wi-Fi icon and select **Download PCAP file**. Save the actual `wokwi.pcap` with the experiment date/scenario.
5. Open it in Wireshark. Wokwi timestamps use simulated time, which may progress slower than wall time.

The free public gateway handles outbound connections. A local host Wireshark capture of the browser may only show the browser-to-gateway tunnel, not the emulated ESP32's inner packets. Use the simulator's own exported capture to study those packets. Never fabricate a capture or assume a feature succeeded without examining real traffic.

## Useful display filters

| Filter | Observe |
|---|---|
| `wlan` | 802.11 frames in a Wokwi PCAP |
| `dns` | Name queries and replies before cloud/NTP access |
| `udp` or `ntp` | Time synchronization and other datagrams |
| `tcp.flags.syn == 1` | TCP connection establishment |
| `tcp.analysis.retransmission` | Retries; do not equate every retry with an application fault |
| `tls` | TLS handshake, certificates where visible, encrypted application records |
| `http` | Plain HTTP only, when explicitly configured for a controlled lab |
| `tcp.port == 8000` | Local dashboard server packets in a host capture |
| `mqtt` | Only relevant after an actual MQTT transport is added |

This project uses HTTP(S), not MQTT. Do not report MQTT messages in the current capture. HTTPS hides JSON values and bearer tokens; encrypted application payloads cannot be read merely by selecting Follow TCP Stream. Record endpoints, record lengths, timing, reconnects, and TLS behavior instead.

## Local software demonstration capture

On your own computer, start the app, choose the loopback interface in Wireshark, filter for TCP port 8000, then operate dashboard controls. You should see browser GETs every two seconds and command/sensor POSTs. This captures actual browser/server traffic; **it is not an ESP32 radio capture**. A privileged capture tool such as `tcpdump -i lo -w classroom-local.pcap 'tcp port 8000'` is another option on Linux when appropriately permitted. Stop it after the demonstration. Never capture unrelated users' traffic.

## Experiment table for the report

Record the real capture file, interface, source/destination, protocol, elapsed time between telemetry requests (nominal device interval 3 s), command-to-ack delay, observed retransmissions, and whether encryption was used. Expect reconnects after connection loss. NTP must establish time before certificate-verified HTTPS. Do not disable certificate verification to make a TLS capture succeed.

No PCAP is bundled: screenshots or packets from an unperformed experiment would not be legitimate evidence. Fill the report with measurements from your own saved capture.
