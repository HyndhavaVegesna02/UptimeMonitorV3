# STORY-122 — live /api/v1 sample responses (captured 2026-07-21 from the running local stack)

Captured from http://localhost:8000 against DynamoDB Local + live Dynatrace loop. Signal key = `http-check`.
These are REAL responses — use them as the authoritative fixture shapes (checklist: fixtures derive from a real captured sample). The stack is up on :8000 if you want to re-capture.

## GET /api/v1/components
```json
[{"id":"http-check","name":"HTTP Check","status":"operational"}]
```
## GET /api/v1/approvals
```json
[]
```
## GET /api/v1/availability?signal_key=http-check
```json
{"availability_pct":1.0,"completeness_pct":0.1451388888888889,"total_verdicts":102,"passing_verdicts":102,"maintenance_verdicts":0,"gap_verdicts":618,"distinct_locations":2,"window":"24h","computed_at":"2026-07-21T08:00:01.306758Z"}
```
## GET /api/v1/history?signal_key=http-check&limit=8
```json
[{"signal_key":"http-check","observed_at":"2026-07-21T07:58:41.133000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000060","latency_ms":588,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:57:41.375000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000047","latency_ms":951,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:56:41.164000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000047","latency_ms":293,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:56:41.164000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000060","latency_ms":561,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:54:41.274000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000060","latency_ms":570,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:53:41.570000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000047","latency_ms":331,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:52:41.508000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000060","latency_ms":904,"response_status_code":200,"check_type":"http"},{"signal_key":"http-check","observed_at":"2026-07-21T07:51:41.147000Z","health":"up","location":"SYNTHETIC_LOCATION-0000000000000047","latency_ms":356,"response_status_code":200,"check_type":"http"}]
```
## GET /api/v1/maintenance
```json
[]
```
