"""
Tests for corpus ingestion.

SEED: Tests use in-memory data only, no external files.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from phonomicon.core.corpus_models import (
    AffectRecord,
    AnnotatorType,
    AudioFeaturesRecord,
)


class TestAudioFeaturesRecordValidation:
    """Tests for AudioFeaturesRecord validation."""

    def test_create_valid_record(self):
        """Test creating a valid AudioFeaturesRecord."""
        record = AudioFeaturesRecord(
            audio_id="aud_001",
            audio_hash="abc123",
            file_path="audio/raw/test.wav",
            duration_sec=180.0,
            sample_rate=44100,
            channels=2,
            tempo_bpm=120.0,
            loudness_lufs=-14.0,
            spectral_centroid_mean=2500.0,
            transient_density=0.65,
            extraction_seed=42,
            extractor_version="0.1.0",
            extracted_at=datetime.utcnow(),
        )

        assert record.audio_id == "aud_001"
        assert record.duration_sec == 180.0
        assert record.sample_rate == 44100

    def test_record_duration_must_be_positive(self):
        """Test that duration must be positive."""
        with pytest.raises(ValueError):
            AudioFeaturesRecord(
                audio_id="aud_001",
                audio_hash="abc123",
                file_path="audio/raw/test.wav",
                duration_sec=0,  # Invalid: must be > 0
                sample_rate=44100,
                channels=2,
                extraction_seed=42,
                extractor_version="0.1.0",
                extracted_at=datetime.utcnow(),
            )

    def test_record_channels_must_be_positive(self):
        """Test that channels must be >= 1."""
        with pytest.raises(ValueError):
            AudioFeaturesRecord(
                audio_id="aud_001",
                audio_hash="abc123",
                file_path="audio/raw/test.wav",
                duration_sec=180.0,
                sample_rate=44100,
                channels=0,  # Invalid: must be >= 1
                extraction_seed=42,
                extractor_version="0.1.0",
                extracted_at=datetime.utcnow(),
            )


class TestAffectRecordValidation:
    """Tests for AffectRecord validation."""

    def test_create_valid_record(self):
        """Test creating a valid AffectRecord."""
        record = AffectRecord(
            audio_id="aud_001",
            valence=0.5,
            arousal=0.3,
            tension=0.7,
            emotion_tags=["energetic", "tense"],
            context_tags=["action", "intense"],
            confidence=0.85,
            annotator_type=AnnotatorType.MODEL,
            annotator_id="model_v1",
            annotated_at=datetime.utcnow(),
        )

        assert record.audio_id == "aud_001"
        assert record.valence == 0.5
        assert record.annotator_type == AnnotatorType.MODEL

    def test_valence_range_validation(self):
        """Test that valence is bounded [-1, 1]."""
        with pytest.raises(ValueError):
            AffectRecord(
                audio_id="aud_001",
                valence=1.5,  # Invalid: > 1
                arousal=0.3,
                tension=0.7,
                confidence=0.85,
                annotator_type=AnnotatorType.HUMAN,
                annotated_at=datetime.utcnow(),
            )

    def test_confidence_range_validation(self):
        """Test that confidence is bounded [0, 1]."""
        with pytest.raises(ValueError):
            AffectRecord(
                audio_id="aud_001",
                valence=0.5,
                arousal=0.3,
                tension=0.7,
                confidence=1.5,  # Invalid: > 1
                annotator_type=AnnotatorType.HUMAN,
                annotated_at=datetime.utcnow(),
            )


class TestJSONLSerialization:
    """Tests for JSONL serialization of corpus records."""

    def test_audio_features_to_jsonl(self):
        """Test AudioFeaturesRecord JSONL serialization."""
        record = AudioFeaturesRecord(
            audio_id="aud_001",
            audio_hash="abc123",
            file_path="audio/raw/test.wav",
            duration_sec=180.0,
            sample_rate=44100,
            channels=2,
            extraction_seed=42,
            extractor_version="0.1.0",
            extracted_at=datetime.utcnow(),
        )

        # Serialize to JSON string (JSONL format)
        json_str = record.model_dump_json()

        # Parse back
        data = json.loads(json_str)
        assert data["audio_id"] == "aud_001"
        assert data["duration_sec"] == 180.0

        # Deserialize back to model
        parsed_record = AudioFeaturesRecord.model_validate(data)
        assert parsed_record.audio_id == record.audio_id
        assert parsed_record.duration_sec == record.duration_sec

    def test_affect_record_to_jsonl(self):
        """Test AffectRecord JSONL serialization."""
        record = AffectRecord(
            audio_id="aud_001",
            valence=0.5,
            arousal=0.3,
            tension=0.7,
            confidence=0.85,
            annotator_type=AnnotatorType.MODEL,
            annotated_at=datetime.utcnow(),
        )

        # Serialize and deserialize
        json_str = record.model_dump_json()
        data = json.loads(json_str)
        parsed_record = AffectRecord.model_validate(data)

        assert parsed_record.audio_id == record.audio_id
        assert parsed_record.valence == record.valence
        assert parsed_record.annotator_type == record.annotator_type
