"""
Phonomicon Overlay HTTP Server.

ABX-Core: Stable HTTP interface reduces integration complexity.
SEED: Deterministic JSON responses with embedded provenance.

Usage:
    python -m phonomicon_overlay.server --host 127.0.0.1 --port 8794

Endpoints:
    GET  /health - Health check
    POST /run    - Execute capability

Capabilities:
    - phonomicon.ping   : Test connectivity
    - phonomicon.echo   : Echo input (testing)
    - phonomicon.mint   : Mint audio to NFT (requires binding)
    - phonomicon.render : Render visual from audio (requires binding)
    - phonomicon.verify : Verify manifest provenance (requires binding)
"""

from __future__ import annotations

import argparse
import json
import socketserver
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict, Tuple

from .provenance import make_provenance

JSON_CT = "application/json; charset=utf-8"


# ============================================================
# INTERNAL PHONOMICON BINDING
# ============================================================
def _try_import_phonomicon_core():
    """
    Bind Phonomicon's REAL entrypoints here.

    ABX-Core: Explicit binding reduces silent failure ambiguity.
    SEED: No hallucinated APIs - all bindings are explicit.

    Example binding (replace with real imports):
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
            # Log error, return None for unbound capabilities
            return {"mint": None, "render": None, "verify": None}

    Until wired, mint/render/verify return structured errors
    explaining what needs to be bound.
    """
    try:
        # TODO: Wire real Phonomicon entrypoints here
        # from phonomicon.services.mint import mint_asset
        # from phonomicon.services.visual import render_visual
        # from phonomicon.core.provenance import verify_provenance_chain
        return {"mint": None, "render": None, "verify": None}
    except Exception:
        return {"mint": None, "render": None, "verify": None}


_CORE = _try_import_phonomicon_core()


# ============================================================
# HTTP HELPERS
# ============================================================
def _read_json(handler: BaseHTTPRequestHandler) -> Dict[str, Any]:
    """
    Read and parse JSON from HTTP request body.

    ABX-Core: Strict JSON validation reduces parsing ambiguity.
    """
    length = int(handler.headers.get("Content-Length", "0"))
    raw = handler.rfile.read(length) if length > 0 else b"{}"
    obj = json.loads(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("root must be object")
    return obj


def _write_json(handler: BaseHTTPRequestHandler, status: int, body: Dict[str, Any]) -> None:
    """
    Write JSON response to HTTP client.

    SEED: Deterministic JSON serialization (sorted keys).
    """
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", JSON_CT)
    handler.send_header("Content-Length", str(len(raw)))
    handler.end_headers()
    handler.wfile.write(raw)


# ============================================================
# CAPABILITY ROUTER
# ============================================================
def _capability_router(cap: str, payload: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
    """
    Route capability requests to appropriate handlers.

    ABX-Core: Explicit routing reduces dispatch ambiguity.
    SEED: All capabilities return structured, deterministic responses.

    Args:
        cap: Capability identifier (e.g., "phonomicon.ping")
        payload: Input parameters

    Returns:
        Tuple of (success: bool, result: dict)
    """

    # ============================================================
    # PING - Test connectivity and binding status
    # ============================================================
    if cap == "phonomicon.ping":
        return True, {
            "pong": True,
            "mint_bound": _CORE.get("mint") is not None,
            "render_bound": _CORE.get("render") is not None,
            "verify_bound": _CORE.get("verify") is not None,
        }

    # ============================================================
    # ECHO - Echo input for testing
    # ============================================================
    if cap == "phonomicon.echo":
        return True, {"echo": payload}

    # ============================================================
    # MINT - Mint audio to NFT
    # ============================================================
    if cap == "phonomicon.mint":
        fn = _CORE.get("mint")
        if fn is None:
            return False, {
                "message": "Phonomicon mint not wired",
                "expected_input": {
                    "audio_id": "string (reference to corpus audio)",
                    "audio_hash": "string (SHA256 of audio file)",
                    "title": "string",
                    "description": "string",
                    "creator": "string",
                    "collection_id": "optional string",
                    "chain": "optional string (blockchain identifier)",
                    "seed": "optional int (for deterministic processing)",
                },
                "action": "Bind mint_asset function in _try_import_phonomicon_core()",
                "example_binding": "from phonomicon.services.mint import mint_asset",
            }

        # TODO: Once wired, adapt payload to mint_asset signature
        # Example:
        # try:
        #     result = await fn(
        #         audio_id=payload["audio_id"],
        #         audio_hash=payload["audio_hash"],
        #         symbolic_profile=...,  # Need to analyze first
        #         visual_artifact=...,   # Need to render first
        #         title=payload["title"],
        #         description=payload["description"],
        #         creator=payload["creator"],
        #         collection_id=payload.get("collection_id"),
        #         chain=payload.get("chain"),
        #     )
        #     return True, {
        #         "manifest_id": result.manifest.manifest_id,
        #         "verified": result.verified,
        #         "manifest": result.manifest.model_dump(),
        #     }
        # except Exception as e:
        #     return False, {"error": str(e)}

        return False, {"message": "mint wired but not implemented"}

    # ============================================================
    # RENDER - Render visual from audio
    # ============================================================
    if cap == "phonomicon.render":
        fn = _CORE.get("render")
        if fn is None:
            return False, {
                "message": "Phonomicon render not wired",
                "expected_input": {
                    "audio_id": "string (reference to corpus audio)",
                    "audio_hash": "string (SHA256 of audio file)",
                    "style": "string (generative|collage|symbolic|abstract)",
                    "dimensions": "optional [width, height] (default: [1024, 1024])",
                    "seed": "optional int (for deterministic rendering)",
                },
                "action": "Bind render_visual function in _try_import_phonomicon_core()",
                "example_binding": "from phonomicon.services.visual import render_visual",
            }

        # TODO: Once wired, adapt payload to render_visual signature
        # Example:
        # try:
        #     from phonomicon.core.schemas import VisualStyle
        #     style = VisualStyle(payload.get("style", "generative"))
        #     dimensions = tuple(payload.get("dimensions", [1024, 1024]))
        #     seed = payload.get("seed")
        #
        #     # Need to analyze audio first to get symbolic_profile
        #     # profile = await analyze_audio(...)
        #
        #     artifact = await fn(
        #         symbolic_profile=profile,
        #         style=style,
        #         dimensions=dimensions,
        #         seed=seed,
        #     )
        #     return True, {
        #         "artifact_id": artifact.artifact_id,
        #         "artifact": artifact.model_dump(),
        #     }
        # except Exception as e:
        #     return False, {"error": str(e)}

        return False, {"message": "render wired but not implemented"}

    # ============================================================
    # VERIFY - Verify manifest provenance
    # ============================================================
    if cap == "phonomicon.verify":
        fn = _CORE.get("verify")
        if fn is None:
            return False, {
                "message": "Phonomicon verify not wired",
                "expected_input": {
                    "manifest": "dict (MintManifest object)",
                    "checks": "optional list[str] (specific checks to run)",
                },
                "action": "Bind verify_provenance_chain function in _try_import_phonomicon_core()",
                "example_binding": "from phonomicon.core.provenance import verify_provenance_chain",
            }

        # TODO: Once wired, adapt payload to verify_provenance_chain signature
        # Example:
        # try:
        #     from phonomicon.core.schemas import MintManifest
        #     manifest = MintManifest.model_validate(payload["manifest"])
        #     valid = fn(manifest)
        #     return True, {
        #         "valid": valid,
        #         "manifest_id": manifest.manifest_id,
        #     }
        # except Exception as e:
        #     return False, {"error": str(e)}

        return False, {"message": "verify wired but not implemented"}

    # ============================================================
    # UNKNOWN CAPABILITY
    # ============================================================
    return False, {
        "message": f"unknown capability: {cap}",
        "known": [
            "phonomicon.ping",
            "phonomicon.echo",
            "phonomicon.mint",
            "phonomicon.render",
            "phonomicon.verify",
        ],
    }


# ============================================================
# HTTP SERVER
# ============================================================
class PhonomiconOverlayHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for Phonomicon overlay.

    ABX-Core: Stable HTTP interface reduces client integration complexity.
    """

    server_version = "phonomicon-overlay/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        """Suppress default logging."""
        return

    def do_GET(self) -> None:
        """
        Handle GET requests.

        Only /health is supported.
        """
        if self.path == "/health":
            _write_json(self, 200, {"ok": True, "service": "phonomicon_overlay"})
            return
        _write_json(self, 404, {"ok": False, "error": "not found"})

    def do_POST(self) -> None:
        """
        Handle POST requests.

        Only /run is supported.

        Request format:
        {
            "capability": "phonomicon.ping|echo|mint|render|verify",
            "input": {...},
            "seed": "optional string"
        }

        Response format:
        {
            "ok": true|false,
            "result": {...} | null,
            "error": {...} | null,
            "provenance": {
                "run_id": "...",
                "ts_utc": "...",
                "payload_hash": "...",
                "env": {...}
            }
        }
        """
        if self.path != "/run":
            _write_json(self, 404, {"ok": False, "error": "not found"})
            return

        try:
            req = _read_json(self)
        except Exception as e:
            _write_json(self, 400, {"ok": False, "error": f"invalid json: {e}"})
            return

        cap = req.get("capability", "phonomicon.echo")
        seed = req.get("seed")
        input_payload = req.get("input", {})
        if not isinstance(input_payload, dict):
            _write_json(self, 400, {"ok": False, "error": "input must be an object"})
            return

        # Generate provenance
        prov = make_provenance("phonomicon", cap, input_payload, seed=seed).to_dict()

        # Route capability
        ok, out = _capability_router(cap, input_payload)

        # Return response
        if ok:
            _write_json(
                self,
                200,
                {
                    "ok": True,
                    "result": out,
                    "error": None,
                    "provenance": prov,
                },
            )
        else:
            _write_json(
                self,
                200,
                {
                    "ok": False,
                    "result": None,
                    "error": out,
                    "provenance": prov,
                },
            )


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """
    Threaded HTTP server for handling concurrent requests.

    ABX-Core: Threading reduces request queuing latency.
    """

    daemon_threads = True


def main() -> None:
    """
    Main entry point for Phonomicon overlay server.

    Usage:
        python -m phonomicon_overlay.server --host 127.0.0.1 --port 8794
    """
    ap = argparse.ArgumentParser(description="Phonomicon Overlay HTTP Server")
    ap.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    ap.add_argument("--port", type=int, default=8794, help="Port to bind to")
    args = ap.parse_args()

    print(f"Starting Phonomicon Overlay Server on {args.host}:{args.port}")
    print(f"Endpoints:")
    print(f"  GET  http://{args.host}:{args.port}/health")
    print(f"  POST http://{args.host}:{args.port}/run")
    print(f"\nCapabilities:")
    print(f"  - phonomicon.ping   (always available)")
    print(f"  - phonomicon.echo   (always available)")
    print(f"  - phonomicon.mint   (requires binding)")
    print(f"  - phonomicon.render (requires binding)")
    print(f"  - phonomicon.verify (requires binding)")
    print(f"\nPress Ctrl+C to stop")

    srv = ThreadedHTTPServer((args.host, args.port), PhonomiconOverlayHandler)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
