"""Advisory, read-only host readiness; the wire gate remains authoritative."""


def host_wait_seconds(gate, url, minimum_interval=1):
    host, _, path = gate.paths(url)
    state = gate.read(path)
    interval = max(1.0, float(minimum_interval), float(state.get('minimumIntervalSeconds', 0)),
                   10.0 if host == 'profiles.ucsd.edu' or host.endswith('.profiles.ucsd.edu') else 0)
    remaining = max(float(state.get('lastRequestAt', 0)) + interval,
                    float(state.get('notBeforeEpoch', 0))) - gate.clock()
    current_mono = gate.monotonic()
    previous_mono = state.get('lastRequestMonotonic')
    if previous_mono is not None and 0 <= float(previous_mono) <= current_mono:
        remaining = max(remaining, float(previous_mono) + interval - current_mono)
    cooldown_mono = state.get('notBeforeMonotonic')
    if cooldown_mono is not None and state.get('cooldownSetMonotonic', 0) <= current_mono:
        remaining = max(remaining, float(cooldown_mono) - current_mono)
    return max(0.0, remaining)
