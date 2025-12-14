# Phonomicon Overlay Service

**Stable HTTP interface for Phonomicon integration with Abraxas/AAL-core**

The overlay exposes Phonomicon capabilities through a deterministic HTTP API with embedded provenance tracking.

## Architecture

The overlay follows AAL principles:

- **ABX-Core**: Stable HTTP interface reduces integration complexity
- **SEED**: All operations tracked with cryptographic provenance
- **Explicit Binding**: No silent API guessing - all bindings are explicit

## Running the Server

```bash
# Start on default host/port (127.0.0.1:8794)
python -m phonomicon_overlay

# Custom host/port
python -m phonomicon_overlay --host 0.0.0.0 --port 9000
```

## HTTP API

### GET /health

Health check endpoint.

**Response:**
```json
{
  "ok": true,
  "service": "phonomicon_overlay"
}
```

### POST /run

Execute a capability.

**Request:**
```json
{
  "capability": "phonomicon.ping",
  "input": {},
  "seed": "optional-seed-for-determinism"
}
```

**Response (success):**
```json
{
  "ok": true,
  "result": {...},
  "error": null,
  "provenance": {
    "run_id": "sha256-hash",
    "ts_utc": "2025-01-01T00:00:00+00:00",
    "payload_hash": "sha256-hash",
    "env": {
      "python": "3.11.0",
      "platform": "Linux-4.4.0",
      "git_head": "abc123...",
      "cwd": "/path/to/repo"
    }
  }
}
```

**Response (error):**
```json
{
  "ok": false,
  "result": null,
  "error": {
    "message": "Error description",
    "expected_input": {...},
    "action": "What to do to fix"
  },
  "provenance": {...}
}
```

## Capabilities

### phonomicon.ping

Test connectivity and check binding status.

**Input:** `{}`

**Output:**
```json
{
  "pong": true,
  "mint_bound": false,
  "render_bound": false,
  "verify_bound": false
}
```

### phonomicon.echo

Echo input for testing.

**Input:** Any object

**Output:**
```json
{
  "echo": <input>
}
```

### phonomicon.mint

Mint audio to NFT (requires binding).

**Input:**
```json
{
  "audio_id": "aud_001",
  "audio_hash": "sha256-hash",
  "title": "Track Title",
  "description": "Track description",
  "creator": "creator_id",
  "collection_id": "optional",
  "chain": "optional",
  "seed": 42
}
```

**Status:** NOT WIRED (returns error with binding instructions)

### phonomicon.render

Render visual from audio (requires binding).

**Input:**
```json
{
  "audio_id": "aud_001",
  "audio_hash": "sha256-hash",
  "style": "generative",
  "dimensions": [1024, 1024],
  "seed": 42
}
```

**Status:** NOT WIRED (returns error with binding instructions)

### phonomicon.verify

Verify manifest provenance (requires binding).

**Input:**
```json
{
  "manifest": {...},
  "checks": ["hash", "signature"]
}
```

**Status:** NOT WIRED (returns error with binding instructions)

## Wiring Real Phonomicon Functions

The overlay is intentionally **not wired** to real Phonomicon services. This prevents silent API hallucination.

To wire capabilities, edit `phonomicon_overlay/server.py`:

### 1. Bind Functions

Edit `_try_import_phonomicon_core()`:

```python
def _try_import_phonomicon_core():
    try:
        from phonomicon.services.mint import mint_asset
        from phonomicon.services.visual import render_visual
        from phonomicon.core.provenance import verify_provenance_chain

        return {
            "mint": mint_asset,
            "render": render_visual,
            "verify": verify_provenance_chain,
        }
    except ImportError as e:
        # Log error
        return {"mint": None, "render": None, "verify": None}
```

### 2. Adapt Payload to Function Signature

Edit the capability handlers in `_capability_router()`:

**Example for mint:**

```python
if cap == "phonomicon.mint":
    fn = _CORE.get("mint")
    if fn is None:
        return False, {"message": "Not wired..."}

    try:
        # First analyze audio to get symbolic_profile
        from phonomicon.services.analytics import analyze_audio
        from phonomicon.core.schemas import ResonanceFrame, EventType

        frame = ResonanceFrame(
            frame_id=f"rf_{payload['audio_id']}",
            event_type=EventType.AUDIO,
            audio_id=payload["audio_id"],
            audio_hash=payload["audio_hash"],
            source_module="phonomicon_overlay",
        )

        profile = await analyze_audio(frame, seed=payload.get("seed"))

        # Then render visual
        artifact = await render_visual(profile, seed=payload.get("seed"))

        # Finally mint
        receipt = await fn(
            audio_id=payload["audio_id"],
            audio_hash=payload["audio_hash"],
            symbolic_profile=profile,
            visual_artifact=artifact,
            title=payload["title"],
            description=payload["description"],
            creator=payload["creator"],
            collection_id=payload.get("collection_id"),
            chain=payload.get("chain"),
        )

        return True, {
            "manifest_id": receipt.manifest.manifest_id,
            "verified": receipt.verified,
            "manifest": receipt.manifest.model_dump(),
        }
    except Exception as e:
        return False, {"error": str(e)}
```

### 3. Handle Async Functions

The current server is synchronous. To support async Phonomicon functions:

**Option A:** Use `asyncio.run()` in the capability router:

```python
import asyncio

def _capability_router(cap: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    if cap == "phonomicon.mint":
        fn = _CORE.get("mint")
        if fn is None:
            return False, {"message": "Not wired"}

        # Run async function
        try:
            result = asyncio.run(_run_mint(fn, payload))
            return True, result
        except Exception as e:
            return False, {"error": str(e)}

async def _run_mint(fn, payload):
    # Async implementation here
    ...
```

**Option B:** Convert the entire server to async (recommended):

Use `aiohttp` or FastAPI instead of stdlib HTTP server.

## Testing the Overlay

### 1. Test Health

```bash
curl http://localhost:8794/health
```

### 2. Test Ping

```bash
curl -X POST http://localhost:8794/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "phonomicon.ping",
    "input": {}
  }'
```

### 3. Test Echo

```bash
curl -X POST http://localhost:8794/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "phonomicon.echo",
    "input": {"message": "Hello, Phonomicon!"}
  }'
```

### 4. Test Unwired Capability

```bash
curl -X POST http://localhost:8794/run \
  -H "Content-Type: application/json" \
  -d '{
    "capability": "phonomicon.mint",
    "input": {
      "audio_id": "aud_001",
      "audio_hash": "abc123",
      "title": "Test",
      "description": "Test",
      "creator": "test"
    }
  }'
```

Should return structured error with binding instructions.

## Provenance Tracking

Every `/run` request generates deterministic provenance:

- **run_id**: SHA256 hash of (overlay, capability, payload_hash, salt)
- **ts_utc**: UTC timestamp in ISO format
- **payload_hash**: SHA256 hash of canonical JSON input
- **env**: Python version, platform, git HEAD, cwd

This ensures:
- **Reproducibility**: Same input + seed = same run_id
- **Traceability**: Cryptographic audit trail
- **Transparency**: Environment capture for debugging

## Integration with AAL-Core

The overlay is designed to integrate seamlessly with aal-core:

1. **Start overlay server** (separate from main Phonomicon API)
2. **Register with aal-core** via service discovery
3. **AAL-core routes** capabilities to overlay `/run` endpoint
4. **Overlay returns** structured JSON with provenance
5. **AAL-core aggregates** results from multiple overlays

## Design Principles

### 1. Explicit Over Implicit

The overlay **refuses to guess** internal Phonomicon APIs. All bindings are explicit in code.

### 2. Structured Error Messages

Unwired capabilities return:
- What's missing
- Expected input format
- How to wire it
- Example binding code

### 3. Deterministic Provenance

All operations tracked with:
- Cryptographic hashes
- UTC timestamps
- Environment fingerprints
- Git provenance

### 4. No Silent Failures

Every error is structured and actionable. No silent fallbacks or magic behavior.

## Next Steps

1. **Test overlay** with ping/echo capabilities
2. **Wire real functions** in `_try_import_phonomicon_core()`
3. **Adapt payloads** in capability handlers
4. **Handle async** with asyncio or aiohttp
5. **Register with aal-core** for service discovery
6. **Add authentication** if needed (API keys, JWT)
7. **Add rate limiting** for production deployment

## Troubleshooting

### "mint_bound": false in ping response

The mint function is not wired. Edit `_try_import_phonomicon_core()` to import real function.

### "invalid json" error

Ensure request has `Content-Type: application/json` header.

### "unknown capability" error

Check capability name spelling. Use `phonomicon.ping` to see available capabilities.

### Server won't start

Check if port is already in use:
```bash
lsof -i :8794
```

## License

MIT (same as Phonomicon)
