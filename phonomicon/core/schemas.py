"""
Core schemas for Phonomicon.

SEED Framework principles:
- All models are deterministic and fully specified
- No hidden state or magic defaults
- Provenance information embedded where needed
- Type-safe with Pydantic validation
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class EventType(str, Enum):
    """Types of events that can be represented in a ResonanceFrame."""

    AUDIO = "audio"
    SYMBOLIC = "symbolic"
    VISUAL = "visual"
    CONTROL = "control"


class ResonanceFrame(BaseModel):
    """
    Shared schema for events/audio/symbolic state across AAL ecosystem.

    ABX-Core: Universal frame reduces integration complexity across modules.
    SEED: Deterministic representation with explicit provenance.
    """

    frame_id: str = Field(..., description="Unique identifier for this frame")
    event_type: EventType = Field(..., description="Type of event this frame represents")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="UTC timestamp of frame creation"
    )

    # Audio data (if applicable)
    audio_id: Optional[str] = Field(None, description="Reference to audio asset")
    audio_hash: Optional[str] = Field(None, description="SHA256 hash of audio data")

    # Symbolic representation
    symbolic_data: dict[str, Any] = Field(
        default_factory=dict, description="Symbolic/semantic features"
    )

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    # Provenance (SEED requirement)
    source_module: str = Field(..., description="Module that generated this frame")
    processing_chain: list[str] = Field(
        default_factory=list, description="Chain of modules that processed this frame"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "frame_id": "rf_20250101_123456_abc",
                "event_type": "audio",
                "audio_id": "aud_001",
                "audio_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "symbolic_data": {"tempo": 120, "key": "C"},
                "source_module": "phonomicon",
                "processing_chain": ["phonomicon.analytics"],
            }
        }


class SymbolicAudioProfile(BaseModel):
    """
    Symbolic representation of audio features.

    ABX-Core: Reduces audio complexity to symbolic form for efficient processing.
    SEED: Deterministic feature extraction with explicit seed parameter.
    """

    audio_id: str = Field(..., description="Reference to source audio")
    audio_hash: str = Field(..., description="SHA256 hash of source audio")

    # Temporal features
    duration_sec: float = Field(..., description="Duration in seconds", gt=0)
    sample_rate: int = Field(..., description="Sample rate in Hz", gt=0)
    tempo_bpm: Optional[float] = Field(None, description="Estimated tempo in BPM", ge=0)

    # Spectral features
    loudness_lufs: Optional[float] = Field(None, description="Loudness in LUFS")
    spectral_centroid: Optional[float] = Field(
        None, description="Average spectral centroid in Hz", ge=0
    )
    spectral_rolloff: Optional[float] = Field(
        None, description="Spectral rolloff frequency in Hz", ge=0
    )

    # Structural features
    transient_density: Optional[float] = Field(
        None, description="Density of transients (0-1)", ge=0, le=1
    )
    harmonic_ratio: Optional[float] = Field(
        None, description="Harmonic-to-percussive ratio (0-1)", ge=0, le=1
    )

    # Symbolic mapping
    runes: list[str] = Field(
        default_factory=list, description="Symbolic runes mapped from audio features"
    )
    mythic_axis: Optional[str] = Field(None, description="Position on mythic axis")
    archetype_tags: list[str] = Field(
        default_factory=list, description="Archetypal associations"
    )

    # Provenance (SEED requirement)
    extraction_seed: int = Field(..., description="Seed used for deterministic extraction")
    model_version: str = Field(..., description="Version of extraction model")
    extracted_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of extraction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "audio_id": "aud_001",
                "audio_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                "duration_sec": 180.5,
                "sample_rate": 44100,
                "tempo_bpm": 120.0,
                "loudness_lufs": -14.0,
                "spectral_centroid": 2500.0,
                "transient_density": 0.65,
                "runes": ["ᚱ", "ᚨ", "ᚦ"],
                "mythic_axis": "chaos",
                "archetype_tags": ["warrior", "fire"],
                "extraction_seed": 42,
                "model_version": "0.1.0",
            }
        }


class VisualStyle(str, Enum):
    """Enumeration of visual rendering styles."""

    GENERATIVE = "generative"
    COLLAGE = "collage"
    SYMBOLIC = "symbolic"
    ABSTRACT = "abstract"


class VisualArtifact(BaseModel):
    """
    Visual artifact generated from symbolic audio profile.

    ABX-Core: Deterministic visual rendering reduces randomness (entropy).
    SEED: Fully reproducible with explicit seed and parameters.
    """

    artifact_id: str = Field(..., description="Unique identifier for this artifact")
    source_audio_id: str = Field(..., description="Source audio identifier")
    source_profile_hash: str = Field(..., description="Hash of source SymbolicAudioProfile")

    # Visual properties
    style: VisualStyle = Field(..., description="Rendering style used")
    dimensions: tuple[int, int] = Field(..., description="(width, height) in pixels")
    format: str = Field(..., description="Image format (png, jpg, svg, etc.)")

    # Visual features (for rarity/trait computation)
    palette_tags: list[str] = Field(default_factory=list, description="Color palette tags")
    geometry_tags: list[str] = Field(default_factory=list, description="Geometric elements")
    motion_implied: bool = Field(False, description="Whether motion is implied")

    # Rarity traits
    traits: dict[str, Any] = Field(
        default_factory=dict, description="Trait dictionary for rarity computation"
    )

    # Rendering data (not the actual image, just metadata)
    rendering_params: dict[str, Any] = Field(
        default_factory=dict, description="Parameters used for rendering"
    )

    # Provenance (SEED requirement)
    rendering_seed: int = Field(..., description="Seed used for deterministic rendering")
    renderer_version: str = Field(..., description="Version of rendering engine")
    rendered_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp of rendering"
    )

    # Storage (actual artifact location)
    artifact_url: Optional[str] = Field(None, description="URL or path to rendered artifact")
    artifact_hash: Optional[str] = Field(None, description="SHA256 hash of artifact file")

    @field_validator("dimensions")
    @classmethod
    def validate_dimensions(cls, v: tuple[int, int]) -> tuple[int, int]:
        """Ensure dimensions are positive."""
        if v[0] <= 0 or v[1] <= 0:
            raise ValueError("Dimensions must be positive integers")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "artifact_id": "art_001",
                "source_audio_id": "aud_001",
                "source_profile_hash": "abc123...",
                "style": "generative",
                "dimensions": (1024, 1024),
                "format": "png",
                "palette_tags": ["dark", "crimson", "gold"],
                "geometry_tags": ["fractal", "spiral"],
                "motion_implied": True,
                "traits": {"rarity_tier": "epic", "element": "fire"},
                "rendering_seed": 42,
                "renderer_version": "0.1.0",
            }
        }


class MintManifest(BaseModel):
    """
    Chain-agnostic manifest for minting an asset.

    ABX-Core: Standardized manifest reduces integration complexity across chains.
    SEED: Complete provenance trail from source audio to final artifact.
    """

    manifest_id: str = Field(..., description="Unique identifier for this manifest")

    # Source references
    audio_id: str = Field(..., description="Source audio identifier")
    audio_hash: str = Field(..., description="SHA256 hash of source audio")
    symbolic_profile_hash: str = Field(..., description="Hash of SymbolicAudioProfile")
    visual_artifact_id: str = Field(..., description="Visual artifact identifier")
    visual_artifact_hash: str = Field(..., description="Hash of visual artifact")

    # Mint metadata
    title: str = Field(..., description="Asset title")
    description: str = Field(..., description="Asset description")
    creator: str = Field(..., description="Creator identifier")

    # Runes and symbolic data
    runes: list[str] = Field(..., description="Symbolic runes for this mint")
    mythic_axis: Optional[str] = Field(None, description="Position on mythic axis")
    archetype_tags: list[str] = Field(default_factory=list, description="Archetypal tags")

    # Traits and rarity
    traits: dict[str, Any] = Field(..., description="Trait dictionary for rarity")
    rarity_score: Optional[float] = Field(None, description="Computed rarity score", ge=0)

    # Collection information
    collection_id: Optional[str] = Field(None, description="Collection this belongs to")

    # Provenance (SEED requirement: complete audit trail)
    provenance: dict[str, Any] = Field(
        ..., description="Complete provenance chain from source to mint"
    )

    # Manifest metadata
    manifest_version: str = Field("1.0", description="Manifest schema version")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Manifest creation timestamp"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "manifest_id": "mint_001",
                "audio_id": "aud_001",
                "audio_hash": "e3b0c44...",
                "symbolic_profile_hash": "abc123...",
                "visual_artifact_id": "art_001",
                "visual_artifact_hash": "def456...",
                "title": "Resonance #1: Fire",
                "description": "A sonic journey through chaos",
                "creator": "aal_user_001",
                "runes": ["ᚱ", "ᚨ", "ᚦ"],
                "mythic_axis": "chaos",
                "traits": {"element": "fire", "rarity_tier": "epic"},
                "provenance": {
                    "audio_extracted": "2025-01-01T00:00:00Z",
                    "visual_rendered": "2025-01-01T00:05:00Z",
                },
            }
        }
