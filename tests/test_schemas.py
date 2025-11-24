"""
Tests for core schemas.

SEED: All tests use in-memory data, no external dependencies.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from phonomicon.core.schemas import (
    EventType,
    MintManifest,
    ResonanceFrame,
    SymbolicAudioProfile,
    VisualArtifact,
    VisualStyle,
)


class TestResonanceFrame:
    """Tests for ResonanceFrame schema."""

    def test_create_valid_frame(self):
        """Test creating a valid ResonanceFrame."""
        frame = ResonanceFrame(
            frame_id="rf_test_001",
            event_type=EventType.AUDIO,
            audio_id="aud_001",
            audio_hash="abc123",
            source_module="phonomicon",
        )

        assert frame.frame_id == "rf_test_001"
        assert frame.event_type == EventType.AUDIO
        assert frame.audio_id == "aud_001"
        assert frame.source_module == "phonomicon"
        assert isinstance(frame.timestamp, datetime)
        assert frame.processing_chain == []

    def test_frame_with_symbolic_data(self):
        """Test ResonanceFrame with symbolic data."""
        frame = ResonanceFrame(
            frame_id="rf_test_002",
            event_type=EventType.SYMBOLIC,
            source_module="phonomicon",
            symbolic_data={"tempo": 120, "key": "C", "runes": ["ᚱ", "ᚨ"]},
        )

        assert frame.symbolic_data["tempo"] == 120
        assert frame.symbolic_data["runes"] == ["ᚱ", "ᚨ"]

    def test_frame_requires_frame_id(self):
        """Test that frame_id is required."""
        with pytest.raises(ValidationError):
            ResonanceFrame(
                event_type=EventType.AUDIO,
                source_module="phonomicon",
            )


class TestSymbolicAudioProfile:
    """Tests for SymbolicAudioProfile schema."""

    def test_create_valid_profile(self):
        """Test creating a valid SymbolicAudioProfile."""
        profile = SymbolicAudioProfile(
            audio_id="aud_001",
            audio_hash="abc123",
            duration_sec=180.0,
            sample_rate=44100,
            tempo_bpm=120.0,
            loudness_lufs=-14.0,
            spectral_centroid=2500.0,
            transient_density=0.65,
            runes=["ᚱ", "ᚨ", "ᚦ"],
            mythic_axis="chaos",
            archetype_tags=["warrior", "fire"],
            extraction_seed=42,
            model_version="0.1.0",
        )

        assert profile.audio_id == "aud_001"
        assert profile.duration_sec == 180.0
        assert profile.tempo_bpm == 120.0
        assert len(profile.runes) == 3
        assert profile.extraction_seed == 42

    def test_profile_duration_must_be_positive(self):
        """Test that duration must be positive."""
        with pytest.raises(ValidationError):
            SymbolicAudioProfile(
                audio_id="aud_001",
                audio_hash="abc123",
                duration_sec=-10.0,  # Invalid: negative
                sample_rate=44100,
                extraction_seed=42,
                model_version="0.1.0",
            )

    def test_profile_transient_density_range(self):
        """Test that transient_density is bounded [0, 1]."""
        with pytest.raises(ValidationError):
            SymbolicAudioProfile(
                audio_id="aud_001",
                audio_hash="abc123",
                duration_sec=180.0,
                sample_rate=44100,
                transient_density=1.5,  # Invalid: > 1
                extraction_seed=42,
                model_version="0.1.0",
            )


class TestVisualArtifact:
    """Tests for VisualArtifact schema."""

    def test_create_valid_artifact(self):
        """Test creating a valid VisualArtifact."""
        artifact = VisualArtifact(
            artifact_id="art_001",
            source_audio_id="aud_001",
            source_profile_hash="xyz789",
            style=VisualStyle.GENERATIVE,
            dimensions=(1024, 1024),
            format="png",
            palette_tags=["dark", "crimson"],
            geometry_tags=["fractal", "spiral"],
            motion_implied=True,
            rendering_seed=42,
            renderer_version="0.1.0",
        )

        assert artifact.artifact_id == "art_001"
        assert artifact.style == VisualStyle.GENERATIVE
        assert artifact.dimensions == (1024, 1024)
        assert artifact.motion_implied is True

    def test_artifact_dimensions_must_be_positive(self):
        """Test that dimensions must be positive."""
        with pytest.raises(ValidationError):
            VisualArtifact(
                artifact_id="art_001",
                source_audio_id="aud_001",
                source_profile_hash="xyz789",
                style=VisualStyle.GENERATIVE,
                dimensions=(0, 1024),  # Invalid: width is 0
                format="png",
                rendering_seed=42,
                renderer_version="0.1.0",
            )


class TestMintManifest:
    """Tests for MintManifest schema."""

    def test_create_valid_manifest(self):
        """Test creating a valid MintManifest."""
        manifest = MintManifest(
            manifest_id="mint_001",
            audio_id="aud_001",
            audio_hash="abc123",
            symbolic_profile_hash="def456",
            visual_artifact_id="art_001",
            visual_artifact_hash="ghi789",
            title="Test Mint",
            description="A test mint",
            creator="test_creator",
            runes=["ᚱ", "ᚨ"],
            traits={"element": "fire", "rarity_tier": "epic"},
            provenance={
                "audio": {"audio_id": "aud_001", "audio_hash": "abc123"},
            },
        )

        assert manifest.manifest_id == "mint_001"
        assert manifest.title == "Test Mint"
        assert manifest.creator == "test_creator"
        assert len(manifest.runes) == 2
        assert manifest.traits["element"] == "fire"

    def test_manifest_requires_all_hashes(self):
        """Test that all hash fields are required."""
        with pytest.raises(ValidationError):
            MintManifest(
                manifest_id="mint_001",
                audio_id="aud_001",
                # Missing audio_hash
                symbolic_profile_hash="def456",
                visual_artifact_id="art_001",
                visual_artifact_hash="ghi789",
                title="Test Mint",
                description="A test mint",
                creator="test_creator",
                runes=[],
                traits={},
                provenance={},
            )


class TestSchemaSerializaton:
    """Tests for schema serialization."""

    def test_profile_to_json(self):
        """Test SymbolicAudioProfile JSON serialization."""
        profile = SymbolicAudioProfile(
            audio_id="aud_001",
            audio_hash="abc123",
            duration_sec=180.0,
            sample_rate=44100,
            extraction_seed=42,
            model_version="0.1.0",
        )

        json_str = profile.model_dump_json()
        assert '"audio_id":"aud_001"' in json_str
        assert '"extraction_seed":42' in json_str

    def test_profile_from_dict(self):
        """Test SymbolicAudioProfile from dict."""
        data = {
            "audio_id": "aud_001",
            "audio_hash": "abc123",
            "duration_sec": 180.0,
            "sample_rate": 44100,
            "extraction_seed": 42,
            "model_version": "0.1.0",
            "extracted_at": datetime.utcnow().isoformat(),
        }

        profile = SymbolicAudioProfile.model_validate(data)
        assert profile.audio_id == "aud_001"
        assert profile.extraction_seed == 42
