"""
Corpus models for Phonomicon Meta-Corpus v0.1.

These models define the structure of JSONL records stored in the corpus.

ABX-Core: Explicit schema reduces ambiguity in corpus data.
SEED: All corpus records are validated and traceable.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# AUDIO_CORE
# ============================================================================


class AudioFeaturesRecord(BaseModel):
    """
    Audio features record from corpus/audio/features/.

    SEED: All audio features are derived deterministically with explicit seeds.
    """

    audio_id: str = Field(..., description="Unique audio identifier")
    audio_hash: str = Field(..., description="SHA256 hash of audio file")
    file_path: str = Field(..., description="Relative path from corpus root")

    # Temporal features
    duration_sec: float = Field(..., description="Duration in seconds", gt=0)
    sample_rate: int = Field(..., description="Sample rate in Hz", gt=0)
    channels: int = Field(..., description="Number of audio channels", ge=1)

    # Musical features
    tempo_bpm: Optional[float] = Field(None, description="Estimated tempo in BPM", ge=0)
    key: Optional[str] = Field(None, description="Estimated musical key")
    time_signature: Optional[str] = Field(None, description="Time signature (e.g., '4/4')")

    # Spectral features
    loudness_lufs: Optional[float] = Field(None, description="Integrated loudness in LUFS")
    dynamic_range_db: Optional[float] = Field(None, description="Dynamic range in dB", ge=0)
    spectral_centroid_mean: Optional[float] = Field(
        None, description="Mean spectral centroid in Hz", ge=0
    )
    spectral_rolloff_mean: Optional[float] = Field(
        None, description="Mean spectral rolloff in Hz", ge=0
    )
    zero_crossing_rate: Optional[float] = Field(
        None, description="Zero crossing rate", ge=0, le=1
    )

    # Structural features
    transient_density: Optional[float] = Field(
        None, description="Density of transients (0-1)", ge=0, le=1
    )
    harmonic_ratio: Optional[float] = Field(
        None, description="Harmonic-to-percussive ratio (0-1)", ge=0, le=1
    )

    # Provenance
    extraction_seed: int = Field(..., description="Seed used for feature extraction")
    extractor_version: str = Field(..., description="Version of feature extractor")
    extracted_at: datetime = Field(..., description="Extraction timestamp")


# ============================================================================
# AFFECT_CORE
# ============================================================================


class AnnotatorType(str, Enum):
    """Type of annotator that provided affect labels."""

    HUMAN = "human"
    MODEL = "model"
    HYBRID = "hybrid"


class AffectRecord(BaseModel):
    """
    Affect labels record from corpus/affect/labels.jsonl.

    ABX-Core: Explicit affect annotation reduces subjective ambiguity.
    """

    audio_id: str = Field(..., description="Reference to audio identifier")
    valence: float = Field(..., description="Valence score (-1 to 1)", ge=-1, le=1)
    arousal: float = Field(..., description="Arousal score (-1 to 1)", ge=-1, le=1)
    tension: float = Field(..., description="Tension score (0 to 1)", ge=0, le=1)

    emotion_tags: list[str] = Field(default_factory=list, description="Emotion labels")
    context_tags: list[str] = Field(default_factory=list, description="Context labels")

    confidence: float = Field(..., description="Annotation confidence (0-1)", ge=0, le=1)
    annotator_type: AnnotatorType = Field(..., description="Type of annotator")
    annotator_id: Optional[str] = Field(None, description="Annotator identifier")

    annotated_at: datetime = Field(..., description="Annotation timestamp")


# ============================================================================
# VISUAL_CORE
# ============================================================================


class VisualMetaRecord(BaseModel):
    """
    Visual metadata record from corpus/visual/meta.jsonl.

    ABX-Core: Explicit visual tagging enables deterministic affect-visual linking.
    """

    image_id: str = Field(..., description="Unique image identifier")
    image_hash: str = Field(..., description="SHA256 hash of image file")
    file_path: str = Field(..., description="Relative path from corpus root")

    # Dimensions
    width: int = Field(..., description="Image width in pixels", gt=0)
    height: int = Field(..., description="Image height in pixels", gt=0)
    format: str = Field(..., description="Image format (png, jpg, etc.)")

    # Style tags
    style_tags: list[str] = Field(default_factory=list, description="Visual style tags")
    palette_tags: list[str] = Field(default_factory=list, description="Color palette tags")
    geometry_tags: list[str] = Field(default_factory=list, description="Geometric element tags")

    # Motion and dynamics
    motion_implied: bool = Field(False, description="Whether motion is implied")

    # Affect linking (ranges for matching)
    affect_valence_range: Optional[tuple[float, float]] = Field(
        None, description="Valence range this image matches (-1 to 1)"
    )
    affect_arousal_range: Optional[tuple[float, float]] = Field(
        None, description="Arousal range this image matches (-1 to 1)"
    )

    # Provenance
    source: str = Field(..., description="Source of image (public domain, owned, etc.)")
    license: str = Field(..., description="License type")
    added_at: datetime = Field(..., description="Date added to corpus")


# ============================================================================
# SYMBOLIC_CORE
# ============================================================================


class SymbolicLinkRecord(BaseModel):
    """
    Symbolic link record from corpus/symbolic/links.jsonl.

    SEED: Explicit symbolic mapping provides deterministic audio-to-meaning translation.
    """

    link_id: str = Field(..., description="Unique link identifier")
    audio_id: str = Field(..., description="Reference to audio")
    image_id: Optional[str] = Field(None, description="Optional reference to image")

    # Symbolic elements
    runes: list[str] = Field(..., description="Symbolic runes")
    narrative_phase: Optional[str] = Field(None, description="Narrative phase")
    mythic_axis: Optional[str] = Field(None, description="Position on mythic axis")
    archetype_tags: list[str] = Field(default_factory=list, description="Archetypal tags")

    # Notes
    notes: Optional[str] = Field(None, description="Human-readable notes")

    # Provenance
    created_by: str = Field(..., description="Creator/annotator identifier")
    created_at: datetime = Field(..., description="Creation timestamp")


# ============================================================================
# RARITY_CORE
# ============================================================================


class RarityCollectionRecord(BaseModel):
    """
    Rarity collection configuration from corpus/rarity/collections.jsonl.

    ABX-Core: Explicit trait schema enables deterministic rarity computation.
    """

    collection_id: str = Field(..., description="Unique collection identifier")
    collection_name: str = Field(..., description="Collection name")

    # Trait schema (defines what traits exist)
    trait_schema: dict[str, list[str]] = Field(
        ..., description="Mapping of trait categories to possible values"
    )

    # Distribution (defines rarity of each trait value)
    trait_distribution: dict[str, dict[str, float]] = Field(
        ..., description="Probability distribution for each trait value"
    )

    # Rarity tiers (optional)
    rarity_tiers: Optional[dict[str, tuple[float, float]]] = Field(
        None, description="Mapping of tier names to score ranges"
    )

    # Notes
    rarity_notes: Optional[str] = Field(None, description="Notes on rarity computation")

    # Market links (optional)
    market_links: Optional[dict[str, str]] = Field(
        None, description="Links to marketplaces or contracts"
    )

    created_at: datetime = Field(..., description="Creation timestamp")


# ============================================================================
# PROVENANCE_CORE
# ============================================================================


class MintRecord(BaseModel):
    """
    Mint provenance record from corpus/provenance/mints.jsonl.

    SEED: Complete audit trail from source to on-chain artifact.
    """

    mint_id: str = Field(..., description="Unique mint identifier")

    # Source hashes (SEED: cryptographic proof of inputs)
    audio_hash: str = Field(..., description="SHA256 hash of source audio")
    image_hash: str = Field(..., description="SHA256 hash of visual artifact")
    manifest_hash: str = Field(..., description="SHA256 hash of mint manifest")
    sap_hash: str = Field(..., description="SHA256 hash of SymbolicAudioProfile")

    # Symbolic data
    runes: list[str] = Field(..., description="Runes for this mint")

    # Chain information (optional until minted on-chain)
    chain: Optional[str] = Field(None, description="Blockchain identifier")
    contract_address: Optional[str] = Field(None, description="Contract address")
    token_id: Optional[str] = Field(None, description="Token ID on chain")
    transaction_hash: Optional[str] = Field(None, description="Transaction hash")

    # Wallet and creator
    wallet_address: Optional[str] = Field(None, description="Minter wallet address")
    creator_id: str = Field(..., description="Creator identifier")

    # Timestamps
    created_at: datetime = Field(..., description="Manifest creation timestamp")
    minted_at: Optional[datetime] = Field(None, description="On-chain mint timestamp")


# ============================================================================
# USER_FLOW_CORE
# ============================================================================


class UXEventType(str, Enum):
    """Types of UX events."""

    PAGE_VIEW = "page_view"
    AUDIO_UPLOAD = "audio_upload"
    ANALYSIS_START = "analysis_start"
    ANALYSIS_COMPLETE = "analysis_complete"
    VISUAL_RENDER = "visual_render"
    MINT_REQUEST = "mint_request"
    MINT_COMPLETE = "mint_complete"


class UXEvent(BaseModel):
    """Individual UX event within a session."""

    event_type: UXEventType = Field(..., description="Type of event")
    timestamp: datetime = Field(..., description="Event timestamp")
    data: Optional[dict[str, Any]] = Field(None, description="Optional event-specific data")


class UXSessionRecord(BaseModel):
    """
    UX session record from corpus/ux/sessions.jsonl.

    ABX-Core: Anonymous UX traces enable product optimization without PII.
    """

    session_id: str = Field(..., description="Anonymous session identifier")
    events: list[UXEvent] = Field(..., description="Chronological list of events")

    session_start: datetime = Field(..., description="Session start timestamp")
    session_end: Optional[datetime] = Field(None, description="Session end timestamp")


# ============================================================================
# METRICS_CORE
# ============================================================================


class ObjectType(str, Enum):
    """Types of objects that can have metrics."""

    AUDIO = "audio"
    VISUAL = "visual"
    MINT = "mint"
    COLLECTION = "collection"


class MetricsRecord(BaseModel):
    """
    Metrics record from corpus/metrics/metrics.jsonl.

    ABX-Core: Explicit metrics enable quantitative optimization.
    These are AAL-specific metrics mentioned in the context.
    """

    object_type: ObjectType = Field(..., description="Type of object being measured")
    object_id: str = Field(..., description="Identifier of the object")

    # AAL-specific metrics
    SDR: Optional[float] = Field(None, description="Signal-to-Distortion Ratio")
    MSI: Optional[float] = Field(None, description="Metric Synthesis Index")
    ARF: Optional[float] = Field(None, description="Artifact Resonance Factor")
    NMC: Optional[float] = Field(None, description="Narrative Mapping Coherence")
    RFR: Optional[float] = Field(None, description="Rarity Factor Rating")
    H_sigma: Optional[float] = Field(None, description="Entropy sigma")
    lambda_N: Optional[float] = Field(None, description="Lambda normalization")
    ITC: Optional[float] = Field(None, description="Information Theory Coefficient")

    # Custom metrics
    custom_metrics: dict[str, float] = Field(
        default_factory=dict, description="Additional custom metrics"
    )

    # Provenance
    computed_at: datetime = Field(..., description="Computation timestamp")
    model_version: str = Field(..., description="Metrics model version")
