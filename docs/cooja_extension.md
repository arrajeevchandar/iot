# Optional Cooja / Contiki-NG extension

This is an experiment design, not an implemented Cooja firmware or a required dependency. Cooja does not emulate this Arduino ESP32 firmware unchanged. Use separate Contiki-NG motes to represent classrooms and carry equivalent telemetry.

## Topology

```text
Classroom 101 ─┐
Classroom 102 ─┼─ RPL/6LoWPAN → Border router → UDP collector
Classroom 103 ─┘                                → HTTP dashboard adapter
```

1. Install Contiki-NG/Cooja from its official source in a suitable Linux environment, following the version's documented Java and toolchain requirements.
2. Start with the supplied RPL/UDP examples and create one border-router mote plus three sensor motes. Configure each sender with a unique room ID and fixed-seed generated temperature/humidity/brightness/air/occupancy payloads.
3. Send a sequence number and timestamp every five seconds. Keep the complete payload small enough to avoid unnecessary 6LoWPAN fragmentation. Record the exact radio medium and seed.
4. Use a host UDP collector to translate the datagrams into the dashboard telemetry schema, with normal authentication. Do not identify a Cooja mote as actual ESP32 hardware in the report.
5. Compare direct and multihop placements. Increase interference/radio loss in controlled steps. Save the `.csc` configuration, source code, logs, and actual captures for each run.

## Measurements

Count packets sent and received using sequence numbers; packet-delivery ratio = received unique sequences / sent sequences. Record end-to-end delay, route changes, hop count, and parent selection. Inspect ICMPv6/RPL and UDP in Wireshark where the chosen Cooja configuration supports exporting captures. RPL is a routing protocol for low-power and lossy networks; ESP32 Wi-Fi in the primary project does not use it.

The extension explores networking topology independently of Wokwi's single Wi-Fi classroom. It should not be listed as completed unless the motes, collector, experiments, and measurements are actually produced.
