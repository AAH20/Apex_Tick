# Gates for measured hardware claims

1. Freeze a workload, wire layouts, integrity policy and state-transition specification.
2. Verify the decoder, normalized core, terminal handling and output serializer against an independent reference; add formal properties where their assumptions are supportable.
3. Integrate an exact board and IP revision, retaining clocks, constraints, source, tool versions, resource reports and physical timing.
4. Calibrate external observation, register input/output boundaries, measure instrument uncertainty and characterize the board's I/O floor.
5. Measure offered/accepted/completed traffic, loss, chronological tails, backpressure, same-instrument hazards, malformed frames, sequence faults and recovery.
6. Emit an Apex_PerfAtlas manifest with raw artifacts and limitations. Only compatible, valid measured runs qualify for comparisons.
7. A licensed STAC comparison additionally requires the applicable authorized specification and the actual independent report when claiming STAC validation.

A nanosecond goal is preregistered only after the platform I/O floor and physical feasibility are established. Simulation clock periods are testbench stimulus and are never used as measured device latency.
