# Phonomicon

**Sound-to-Art Minting Platform for Applied Alchemy Labs (AAL)**

Phonomicon transforms original audio into symbolic profiles and visual artifacts, creating chain-agnostic NFT manifests with complete provenance trails.

## Overview

Phonomicon is a modular component of the **Applied Alchemy Labs (AAL)** ecosystem, implementing:

- **ABX-Core v1.2**: Modular, structured, deterministic architecture where every added complexity reduces applied metrics (compute, time, cost, or entropy)
- **SEED Framework**: Deterministic execution, embedded provenance, no magic side effects, and no fake/mock data in the library itself
- **ERS Scheduling**: Entropy-Reducing Scheduler for GPU and heavy computational tasks
- **ResonanceFrame Protocol**: Shared schema for inter-module communication with aal-core

### What Phonomicon Does

1. **Audio Analysis** (`analyze_audio`): Extracts symbolic profiles from audio files
   - Temporal features (duration, tempo, sample rate)
   - Spectral features (loudness, centroid, rolloff)
   - Structural features (transient density, harmonic ratio)
   - Symbolic mapping to runes and mythic axes

2. **Visual Rendering** (`render_visual`): Generates deterministic visual artifacts from symbolic profiles
   - Multiple rendering styles (generative, collage, symbolic, abstract)
   - Deterministic with explicit seed parameters
   - Trait extraction for rarity computation

3. **Asset Minting** (`mint_asset`): Creates chain-agnostic mint manifests
   - Complete provenance from audio source to visual artifact
   - Cryptographic hashing (SHA256) for immutable references
   - Trait-based rarity scoring
   - Verification of provenance chains

## Architecture

```
phonomicon/
├── core/                   # Core schemas and models
│   ├── schemas.py          # ResonanceFrame, SymbolicAudioProfile, VisualArtifact, MintManifest
│   ├── corpus_models.py    # All corpus record types (8 cores)
│   └── provenance.py       # Hashing, manifest building, verification
├── services/               # Business logic
│   ├── analytics.py        # Audio analysis service
│   ├── visual.py           # Visual rendering service
│   └── mint.py             # Minting service
├── infra/                  # Infrastructure
│   ├── scheduler.py        # ERS (Entropy-Reducing Scheduler)
│   └── bus_client.py       # aal-core message bus client
├── api/                    # FastAPI application
│   └── app.py              # REST endpoints
├── corpus/                 # Data storage (8 cores)
│   ├── audio/              # Audio files and features
│   ├── affect/             # Affect labels
│   ├── visual/             # Images and metadata
│   ├── symbolic/           # Symbolic links
│   ├── rarity/             # Collection schemas
│   ├── provenance/         # Mint records
│   ├── ux/                 # UX sessions
│   └── metrics/            # AAL metrics
└── config/                 # Configuration
    └── settings.py         # Environment-based settings
```

## Installation

### Prerequisites

- Python 3.11+
- Virtual environment (recommended)

### Setup

1. Clone the repository:

```bash
git clone <repository-url>
cd Phonomicon
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -e .
```

4. For development (includes testing and linting):

```bash
pip install -e ".[dev]"
```

## Configuration

Phonomicon uses environment variables for configuration. Create a `.env` file:

```bash
# Application settings
PHONOMICON_ENVIRONMENT=development
PHONOMICON_DEBUG_MODE=true
PHONOMICON_LOG_LEVEL=INFO

# API settings
PHONOMICON_API_HOST=0.0.0.0
PHONOMICON_API_PORT=8000

# AAL-Core integration
PHONOMICON_AAL_CORE_URL=http://localhost:9000
PHONOMICON_AAL_MESSAGE_BUS_URL=http://localhost:9000/bus

# Scheduler settings
PHONOMICON_SCHEDULER_WORKER_THREADS=4
PHONOMICON_SCHEDULER_GPU_ENABLED=false

# Analysis settings (deterministic seeds)
PHONOMICON_AUDIO_ANALYSIS_SEED=42
PHONOMICON_VISUAL_RENDERING_SEED=42
```

All settings have safe defaults and are documented in `phonomicon/config/settings.py`.

## Usage

### Running the API Server

```bash
python -m phonomicon.api.app
```

Or using uvicorn directly:

```bash
uvicorn phonomicon.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

Interactive API docs: `http://localhost:8000/docs`

### API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

#### Analyze Audio

```bash
curl -X POST http://localhost:8000/analyze-audio \
  -H "Content-Type: application/json" \
  -d '{
    "resonance_frame": {
      "frame_id": "rf_001",
      "event_type": "audio",
      "audio_id": "aud_001",
      "audio_hash": "abc123...",
      "source_module": "phonomicon"
    },
    "seed": 42
  }'
```

#### Render Visual

```bash
curl -X POST http://localhost:8000/render-visual \
  -H "Content-Type: application/json" \
  -d '{
    "symbolic_profile": {...},
    "style": "generative",
    "dimensions": [1024, 1024],
    "seed": 42
  }'
```

#### Mint Asset

```bash
curl -X POST http://localhost:8000/mint-asset \
  -H "Content-Type: application/json" \
  -d '{
    "audio_id": "aud_001",
    "audio_hash": "abc123...",
    "symbolic_profile": {...},
    "visual_artifact": {...},
    "title": "Resonance #1",
    "description": "A sonic journey",
    "creator": "user_001"
  }'
```

### Corpus Management

#### Populate Corpus

See `phonomicon/corpus/README.md` for detailed instructions on populating the corpus with:
- Audio files
- Affect labels
- Visual assets
- Symbolic mappings
- Rarity configurations

#### Extract Audio Features

```bash
python scripts/extract_audio_features.py \
  --audio-dir phonomicon/corpus/audio/raw \
  --output-dir phonomicon/corpus/audio/features \
  --seed 42
```

#### Validate Corpus

```bash
python scripts/ingest_corpus.py --validate-only
```

#### Build Corpus Indices

```bash
python scripts/ingest_corpus.py --rebuild-index
```

## Programmatic Usage

```python
import asyncio
from phonomicon import analyze_audio, render_visual, mint_asset
from phonomicon.core.schemas import ResonanceFrame, EventType

async def main():
    # Create a ResonanceFrame
    frame = ResonanceFrame(
        frame_id="rf_001",
        event_type=EventType.AUDIO,
        audio_id="aud_001",
        audio_hash="abc123...",
        source_module="my_app",
    )

    # Analyze audio
    profile = await analyze_audio(frame, seed=42)
    print(f"Extracted runes: {profile.runes}")

    # Render visual
    artifact = await render_visual(profile, seed=42)
    print(f"Artifact ID: {artifact.artifact_id}")

    # Mint asset
    receipt = await mint_asset(
        audio_id="aud_001",
        audio_hash="abc123...",
        symbolic_profile=profile,
        visual_artifact=artifact,
        title="My First Mint",
        description="A test mint",
        creator="my_wallet",
    )

    if receipt.verified:
        print(f"Mint successful: {receipt.manifest.manifest_id}")
    else:
        print(f"Mint failed: {receipt.error}")

asyncio.run(main())
```

## Integration with AAL-Core

Phonomicon integrates with the aal-core hub via:

1. **Message Bus**: Publishes events and consumes ResonanceFrames
2. **ResonanceFrame Protocol**: Universal data structure for inter-module communication
3. **ERS Scheduler**: Coordinates heavy computation with other modules

To enable aal-core integration:

1. Ensure aal-core is running
2. Configure `PHONOMICON_AAL_CORE_URL` in your `.env`
3. The bus client will automatically connect on startup

## Development

### Running Tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=phonomicon --cov-report=html
```

### Code Quality

Format code:

```bash
black phonomicon/ tests/ scripts/
```

Lint code:

```bash
ruff check phonomicon/ tests/ scripts/
```

Type checking:

```bash
mypy phonomicon/
```

## ABX-Core and SEED Principles

### How This Repo Enforces ABX-Core v1.2

1. **Modular Architecture**: Clear separation between core, services, infra, and API
2. **Explicit Complexity**: Every abstraction (scheduler, bus client, provenance) reduces a metric:
   - Scheduler: Reduces compute resource contention
   - Provenance hashing: Reduces artifact ambiguity
   - Corpus indices: Reduces lookup time complexity
   - Configuration centralization: Reduces environment ambiguity

### How This Repo Enforces SEED Framework

1. **Deterministic Execution**: All analysis and rendering uses explicit seeds
2. **Provenance Embedded**: Every artifact (profile, visual, manifest) tracks:
   - Source hashes (SHA256)
   - Model versions
   - Extraction/rendering seeds
   - Timestamps
3. **No Magic Side Effects**: Functions are pure where possible, side effects are explicit
4. **No Mock Data**: Library contains no hard-coded fake data; tests use in-memory objects

### ERS Scheduler

The Entropy-Reducing Scheduler provides:
- Priority-based job queuing (CRITICAL, HIGH, NORMAL, LOW)
- Deterministic execution order (priority + timestamp)
- GPU resource hints (for future GPU scheduling)
- Complete job provenance (created, started, completed)

## Next Steps

### For You (User)

1. ✅ Review the generated repo structure
2. ✅ Install dependencies: `pip install -e ".[dev]"`
3. ✅ Run tests: `pytest`
4. ✅ Start the API: `python -m phonomicon.api.app`
5. ⬜ Populate `phonomicon/corpus/audio/raw/` with real audio files
6. ⬜ Extract features: `python scripts/extract_audio_features.py`
7. ⬜ Add affect labels to `phonomicon/corpus/affect/labels.jsonl`
8. ⬜ Add visual assets to `phonomicon/corpus/visual/`
9. ⬜ Create symbolic links in `phonomicon/corpus/symbolic/links.jsonl`
10. ⬜ Define collections in `phonomicon/corpus/rarity/collections.jsonl`
11. ⬜ Validate corpus: `python scripts/ingest_corpus.py --validate-only`
12. ⬜ Integrate with aal-core message bus (configure `PHONOMICON_AAL_CORE_URL`)

### For Implementation

The following areas are scaffolded with clear interfaces but need real implementations:

1. **Audio Feature Extraction** (`services/analytics.py`):
   - Integrate librosa, essentia, or aubio for real DSP
   - Implement rune mapping algorithm
   - Add GPU support for heavy models

2. **Visual Rendering** (`services/visual.py`):
   - Integrate generative models (StyleGAN, Diffusion)
   - Implement corpus image selection and transformation
   - Add actual image file saving to `corpus/visual/images/`

3. **Rarity Computation** (`services/mint.py`):
   - Load trait schemas from `corpus/rarity/collections.jsonl`
   - Implement statistical rarity formulas
   - Add trait combination bonuses

4. **Corpus Indexing** (`scripts/ingest_corpus.py`):
   - Build in-memory or SQLite indices
   - Create efficient lookup structures (audio_id -> features, etc.)

5. **Bus Client** (`infra/bus_client.py`):
   - Implement WebSocket connection to aal-core
   - Add reconnection logic
   - Handle message serialization/deserialization

## License

MIT

## Contact

For questions or contributions, please open an issue or submit a pull request.

---

**Built with ABX-Core v1.2 and SEED Framework principles.**
**Part of the Applied Alchemy Labs (AAL) ecosystem.**
