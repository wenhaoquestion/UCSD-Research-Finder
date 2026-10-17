# Frame discovery adapter QA

**PASS** — 2026-10-16T05:11:51+00:00. No material issues found. **54/54 independently run offline tests passed**:13 frame discovery,11 shared-adapter,30 original-URI/one-shot/cap tests. The reported199 local/321 full tests were not independently rerun. Actual requests: **0**.

Reviewed adapter SHA `2e691409cab7ec3dff70b9876bc98b9260c2c4af19d9532b65cb4944433a4aea`; frame-test SHA `5e4090edf2ade8dd77e81f90401ce8836a681662c82ee10a3529c369e6693b34` match the assigned pins.

- **actual HTML frame syntax**: Only parsed frame/iframe elements with src qualify; anchors/images, script string content and HTML comments do not. Empty display text is allowed.
- **reviewed provenance and exact request target**: sourceId, aware original observedAt/review time, declared64-hex source body SHA, packet source SHA and actual saved raw SHA are required. The target must equal urljoin(sourceURL, literal src) under strict request_key, with same exact hostname; supplied originalHtmlAttribute must match literally. Scheme/query/trailing-path/explicit-port substitutions against unchanged src fail.
- **access and identity boundary**: Current root must be ok and no explicit root/robots/history 401/403/denial/authentication/challenge boundary may be bypassed. Cached target robots denial or existing target capture uses existing controls. Discovery never accepts entity/science or rewrites root canonical/HTTP redirect proof.
- **network policy unchanged**: Removing exactly18 new plan lines recreates the prior receipt adapter bytes SHA. Only plan AST changed; public safe_url validation and actual HTTP/www preservation, pinned dependency compilation, TLS transport, shared gate, retry/cooldown, durable one-shot journal and individually reviewed8M cap logic are byte/AST unchanged.

Strong preservation check: removing exactly18 newly added plan lines in memory yields `34ebac1ceaf1ba5eae5773b59099b34d993d40aa0135b9698c360a766f3ff02c`, exactly the adapter in the existing network receipt. The only changed function AST is plan; no transmission policy was modified by the frame branch.

The current network receipt still names the pre-frame adapter, so execute remains correctly disabled until the parent creates the new verified receipt. This is the expected hash guard, not an adapter defect. QA did not re-enable or change any receipt. All planner/transport execution during tests used isolated fixtures and mocked transports; production plan/execute was not invoked. Only this QA report pair persists.
