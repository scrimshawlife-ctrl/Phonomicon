# Phonomicon Corpus

This directory contains the **Phonomicon Meta-Corpus v0.1**, which stores all data for sound-to-art minting.

## Directory Structure

```
corpus/
├── audio/
│   ├── raw/              # Original audio files (wav, mp3, flac, etc.)
│   └── features/         # JSONL feature files (one per audio_id)
├── affect/
│   └── labels.jsonl      # Affect annotations (valence, arousal, tension)
├── visual/
│   ├── images/           # Curated images (public domain or owned)
│   └── meta/
│       └── meta.jsonl    # Visual metadata (style, palette, geometry tags)
├── symbolic/
│   └── links.jsonl       # Audio-image-rune symbolic mappings
├── rarity/
│   └── collections.jsonl # Collection trait schemas and distributions
├── provenance/
│   └── mints.jsonl       # Mint provenance records
├── ux/
│   └── sessions.jsonl    # Anonymous UX session traces
└── metrics/
    └── metrics.jsonl     # AAL-specific metrics (SDR, MSI, ARF, etc.)
```

## Populating the Corpus

### 1. Audio Files

Place your original audio files in `audio/raw/`:

```bash
cp my_track.wav corpus/audio/raw/
```

Then extract features:

```bash
python scripts/extract_audio_features.py --audio-dir corpus/audio/raw
```

This will generate `corpus/audio/features/{audio_id}.jsonl` files.

### 2. Affect Labels

Create affect annotations in `affect/labels.jsonl` (one JSON object per line):

```json
{"audio_id": "aud_001", "valence": 0.5, "arousal": 0.7, "tension": 0.6, "emotion_tags": ["energetic", "tense"], "context_tags": ["action"], "confidence": 0.9, "annotator_type": "human", "annotated_at": "2025-01-01T00:00:00Z"}
```

### 3. Visual Assets

Place curated images in `visual/images/` and create metadata records in `visual/meta/meta.jsonl`:

```json
{"image_id": "img_001", "image_hash": "abc123...", "file_path": "visual/images/fractal_001.png", "width": 1024, "height": 1024, "format": "png", "style_tags": ["abstract", "geometric"], "palette_tags": ["dark", "crimson"], "geometry_tags": ["fractal"], "motion_implied": false, "source": "public_domain", "license": "CC0", "added_at": "2025-01-01T00:00:00Z"}
```

### 4. Symbolic Links

Create symbolic mappings in `symbolic/links.jsonl`:

```json
{"link_id": "link_001", "audio_id": "aud_001", "image_id": "img_001", "runes": ["ᚱ", "ᚨ", "ᚦ"], "mythic_axis": "chaos", "archetype_tags": ["warrior", "fire"], "created_by": "curator", "created_at": "2025-01-01T00:00:00Z"}
```

### 5. Rarity Collections

Define collection trait schemas in `rarity/collections.jsonl`:

```json
{"collection_id": "col_genesis", "collection_name": "Genesis Collection", "trait_schema": {"element": ["fire", "water", "earth", "air", "aether"], "rarity_tier": ["common", "rare", "epic", "legendary"]}, "trait_distribution": {"element": {"fire": 0.25, "water": 0.25, "earth": 0.25, "air": 0.20, "aether": 0.05}, "rarity_tier": {"common": 0.60, "rare": 0.25, "epic": 0.12, "legendary": 0.03}}, "created_at": "2025-01-01T00:00:00Z"}
```

### 6. Provenance

Mint records are automatically created by the API and stored in `provenance/mints.jsonl`.

### 7. UX Sessions

Anonymous UX traces can be logged to `ux/sessions.jsonl` for product analytics.

### 8. Metrics

Metrics are computed and stored in `metrics/metrics.jsonl`.

## Validation

After populating corpus data, validate it:

```bash
python scripts/ingest_corpus.py --validate-only
```

## Important Notes

- **No mock data**: The corpus library itself contains no fake data. You must populate it with real assets.
- **JSONL format**: All metadata files use JSONL (one JSON object per line) for efficient streaming.
- **Validation**: All records are validated against Pydantic schemas defined in `phonomicon.core.corpus_models`.
- **Provenance**: Audio hashes (SHA256) ensure cryptographic traceability from source to mint.
