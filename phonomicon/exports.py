# Phonomicon — Explicit Function Exports (Canonical)
# Role: sound → symbol → artifact minting (analysis + rendering, no custody)

EXPORTS = [
  {
    "id": "phonomicon.op.analyze_audio.v1",
    "name": "Analyze Audio",
    "kind": "overlay_op",
    "version": "1.0.0",
    "owner": "phonomicon",
    "rune": "ᛈᚺᛟ",
    "entrypoint": "phonomicon.logic:analyze_audio",
    "inputs_schema": {
      "type": "object",
      "properties": {
        "audio_path": {"type": "string"},
        "seed": {"type": "integer"}
      },
      "required": ["audio_path"],
      "additionalProperties": true
    },
    "outputs_schema": {
      "type": "object",
      "properties": {
        "features": {"type": "object"},
        "metrics_packet": {"type": "object"}
      },
      "required": ["features"]
    },
    "capabilities": ["cpu", "no_net", "read_only"],
    "cost_hint": {"ms_p50": 120, "ms_p95": 480},
    "provenance": {
      "repo": "phonomicon",
      "commit": "PINNED",
      "artifact_hash": "PINNED",
      "generated_at": 0
    }
  },
  {
    "id": "phonomicon.op.render_artifact.v1",
    "name": "Render Artifact",
    "kind": "overlay_op",
    "version": "1.0.0",
    "owner": "phonomicon",
    "rune": "ᚨᚱᛏ",
    "entrypoint": "phonomicon.logic:render_artifact",
    "inputs_schema": {
      "type": "object",
      "properties": {
        "features": {"type": "object"},
        "style": {"type": "string"},
        "seed": {"type": "integer"}
      },
      "required": ["features", "seed"],
      "additionalProperties": true
    },
    "outputs_schema": {
      "type": "object",
      "properties": {
        "image_path": {"type": "string"},
        "metadata": {"type": "object"}
      },
      "required": ["image_path"]
    },
    "capabilities": ["cpu", "disk_write", "no_net"],
    "cost_hint": {"ms_p50": 300, "ms_p95": 1200},
    "provenance": {
      "repo": "phonomicon",
      "commit": "PINNED",
      "artifact_hash": "PINNED",
      "generated_at": 0
    }
  }
]
