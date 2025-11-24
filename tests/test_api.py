"""
Tests for FastAPI endpoints.

SEED: Tests use in-memory data and FastAPI test client.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from phonomicon.api.app import app
from phonomicon.core.schemas import (
    EventType,
    ResonanceFrame,
    SymbolicAudioProfile,
    VisualArtifact,
    VisualStyle,
)

# Create test client
client = TestClient(app)


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "scheduler_running" in data
        assert "bus_connected" in data


class TestAnalyzeAudioEndpoint:
    """Tests for /analyze-audio endpoint."""

    def test_analyze_audio_success(self):
        """Test successful audio analysis."""
        # Create a valid ResonanceFrame
        frame = ResonanceFrame(
            frame_id="rf_test_001",
            event_type=EventType.AUDIO,
            audio_id="aud_test_001",
            audio_hash="abc123def456",
            source_module="phonomicon",
        )

        # Make request
        response = client.post(
            "/analyze-audio",
            json={"resonance_frame": frame.model_dump(mode="json")},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "symbolic_profile" in data
        profile = data["symbolic_profile"]
        assert profile["audio_id"] == "aud_test_001"
        assert profile["audio_hash"] == "abc123def456"
        assert "runes" in profile
        assert "extraction_seed" in profile

    def test_analyze_audio_with_custom_seed(self):
        """Test audio analysis with custom seed."""
        frame = ResonanceFrame(
            frame_id="rf_test_002",
            event_type=EventType.AUDIO,
            audio_id="aud_test_002",
            audio_hash="xyz789",
            source_module="phonomicon",
        )

        # Make request with custom seed
        response = client.post(
            "/analyze-audio",
            json={
                "resonance_frame": frame.model_dump(mode="json"),
                "seed": 999,
            },
        )

        assert response.status_code == 200
        data = response.json()
        profile = data["symbolic_profile"]
        assert profile["extraction_seed"] == 999

    def test_analyze_audio_missing_audio_id(self):
        """Test analysis with missing audio_id."""
        frame = ResonanceFrame(
            frame_id="rf_test_003",
            event_type=EventType.AUDIO,
            source_module="phonomicon",
            # Missing audio_id
        )

        response = client.post(
            "/analyze-audio",
            json={"resonance_frame": frame.model_dump(mode="json")},
        )

        assert response.status_code == 400


class TestRenderVisualEndpoint:
    """Tests for /render-visual endpoint."""

    def test_render_visual_success(self):
        """Test successful visual rendering."""
        # Create a valid SymbolicAudioProfile
        profile = SymbolicAudioProfile(
            audio_id="aud_test_001",
            audio_hash="abc123",
            duration_sec=180.0,
            sample_rate=44100,
            runes=["ᚱ", "ᚨ"],
            extraction_seed=42,
            model_version="0.1.0",
        )

        # Make request
        response = client.post(
            "/render-visual",
            json={"symbolic_profile": profile.model_dump(mode="json")},
        )

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "visual_artifact" in data
        artifact = data["visual_artifact"]
        assert artifact["source_audio_id"] == "aud_test_001"
        assert "artifact_id" in artifact
        assert "rendering_seed" in artifact

    def test_render_visual_with_custom_params(self):
        """Test visual rendering with custom parameters."""
        profile = SymbolicAudioProfile(
            audio_id="aud_test_002",
            audio_hash="xyz789",
            duration_sec=180.0,
            sample_rate=44100,
            extraction_seed=42,
            model_version="0.1.0",
        )

        # Make request with custom style, dimensions, and seed
        response = client.post(
            "/render-visual",
            json={
                "symbolic_profile": profile.model_dump(mode="json"),
                "style": "symbolic",
                "dimensions": [512, 512],
                "seed": 123,
            },
        )

        assert response.status_code == 200
        data = response.json()
        artifact = data["visual_artifact"]
        assert artifact["style"] == "symbolic"
        assert artifact["dimensions"] == [512, 512]
        assert artifact["rendering_seed"] == 123


class TestMintAssetEndpoint:
    """Tests for /mint-asset endpoint."""

    def test_mint_asset_success(self):
        """Test successful asset minting."""
        # Create required components
        profile = SymbolicAudioProfile(
            audio_id="aud_test_001",
            audio_hash="abc123",
            duration_sec=180.0,
            sample_rate=44100,
            runes=["ᚱ", "ᚨ"],
            mythic_axis="chaos",
            archetype_tags=["warrior"],
            extraction_seed=42,
            model_version="0.1.0",
        )

        artifact = VisualArtifact(
            artifact_id="art_test_001",
            source_audio_id="aud_test_001",
            source_profile_hash="profile_hash_123",
            style=VisualStyle.GENERATIVE,
            dimensions=(1024, 1024),
            format="png",
            rendering_seed=42,
            renderer_version="0.1.0",
        )

        # Make mint request
        response = client.post(
            "/mint-asset",
            json={
                "audio_id": "aud_test_001",
                "audio_hash": "abc123",
                "symbolic_profile": profile.model_dump(mode="json"),
                "visual_artifact": artifact.model_dump(mode="json"),
                "title": "Test Mint",
                "description": "A test mint",
                "creator": "test_creator",
            },
        )

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "manifest" in data
        assert "verified" in data
        manifest = data["manifest"]
        assert manifest["title"] == "Test Mint"
        assert manifest["creator"] == "test_creator"
        assert data["verified"] is True

    def test_mint_asset_with_collection(self):
        """Test minting with collection ID."""
        profile = SymbolicAudioProfile(
            audio_id="aud_test_002",
            audio_hash="xyz789",
            duration_sec=180.0,
            sample_rate=44100,
            extraction_seed=42,
            model_version="0.1.0",
        )

        artifact = VisualArtifact(
            artifact_id="art_test_002",
            source_audio_id="aud_test_002",
            source_profile_hash="profile_hash_456",
            style=VisualStyle.GENERATIVE,
            dimensions=(1024, 1024),
            format="png",
            rendering_seed=42,
            renderer_version="0.1.0",
        )

        response = client.post(
            "/mint-asset",
            json={
                "audio_id": "aud_test_002",
                "audio_hash": "xyz789",
                "symbolic_profile": profile.model_dump(mode="json"),
                "visual_artifact": artifact.model_dump(mode="json"),
                "title": "Test Mint 2",
                "description": "Another test mint",
                "creator": "test_creator",
                "collection_id": "col_genesis",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["manifest"]["collection_id"] == "col_genesis"


class TestSchedulerStatsEndpoint:
    """Tests for /scheduler/stats endpoint."""

    def test_scheduler_stats(self):
        """Test scheduler statistics endpoint."""
        response = client.get("/scheduler/stats")
        assert response.status_code == 200

        data = response.json()
        assert "running" in data
        assert "queue_size" in data
        assert "max_workers" in data
        assert "gpu_enabled" in data
