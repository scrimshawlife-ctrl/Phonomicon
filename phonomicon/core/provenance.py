"""
Provenance utilities for Phonomicon.

SEED Framework: All artifacts must be traceable and reproducible.
ABX-Core: Cryptographic hashing reduces ambiguity in artifact identification.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Union

from pydantic import BaseModel

from phonomicon.config import get_settings


def compute_hash(
    data: Union[bytes, str, BaseModel, dict[str, Any]], algorithm: str = "sha256"
) -> str:
    """
    Compute cryptographic hash of data.

    ABX-Core: Deterministic hashing enables unique artifact identification.
    SEED: Provenance trail depends on immutable hash references.

    Args:
        data: Data to hash (bytes, string, Pydantic model, or dict)
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex-encoded hash digest

    Example:
        >>> compute_hash("hello world")
        'b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9'
    """
    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Hash algorithm '{algorithm}' not available")

    hasher = hashlib.new(algorithm)

    # Convert data to bytes
    if isinstance(data, bytes):
        hash_bytes = data
    elif isinstance(data, str):
        hash_bytes = data.encode("utf-8")
    elif isinstance(data, BaseModel):
        # Pydantic model: serialize to JSON (deterministically)
        hash_bytes = data.model_dump_json(indent=None, sort_keys=True).encode("utf-8")
    elif isinstance(data, dict):
        # Dict: serialize to JSON (deterministically)
        hash_bytes = json.dumps(data, indent=None, sort_keys=True).encode("utf-8")
    else:
        raise TypeError(f"Unsupported data type for hashing: {type(data)}")

    hasher.update(hash_bytes)
    return hasher.hexdigest()


def compute_file_hash(file_path: Union[str, Path], algorithm: str = "sha256") -> str:
    """
    Compute cryptographic hash of a file.

    ABX-Core: File hashing enables content-addressable storage.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm (default: sha256)

    Returns:
        Hex-encoded hash digest

    Raises:
        FileNotFoundError: If file does not exist
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)

    # Read file in chunks to handle large files efficiently
    # ABX-Core: Chunked reading reduces memory cost for large files
    chunk_size = 65536  # 64KB chunks
    with open(path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def generate_provenance_entry(
    source_type: str,
    source_id: str,
    operation: str,
    output_hash: str,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generate a standardized provenance entry.

    SEED: All transformations must be recorded for reproducibility.

    Args:
        source_type: Type of source (audio, visual, manifest, etc.)
        source_id: Identifier of source object
        operation: Operation performed (extract, render, mint, etc.)
        output_hash: Hash of the output artifact
        metadata: Optional additional metadata

    Returns:
        Provenance entry dict

    Example:
        >>> entry = generate_provenance_entry(
        ...     source_type="audio",
        ...     source_id="aud_001",
        ...     operation="extract_features",
        ...     output_hash="abc123...",
        ...     metadata={"seed": 42, "model_version": "0.1.0"}
        ... )
    """
    settings = get_settings()

    entry = {
        "source_type": source_type,
        "source_id": source_id,
        "operation": operation,
        "output_hash": output_hash,
        "metadata": metadata or {},
    }

    # Add timestamp if configured
    if settings.provenance_include_timestamps:
        entry["timestamp"] = datetime.utcnow().isoformat()

    return entry


def create_manifest(
    audio_id: str,
    audio_hash: str,
    symbolic_profile: "SymbolicAudioProfile",  # type: ignore
    visual_artifact: "VisualArtifact",  # type: ignore
    title: str,
    description: str,
    creator: str,
    collection_id: str | None = None,
) -> "MintManifest":  # type: ignore
    """
    Create a complete mint manifest with full provenance chain.

    ABX-Core: Manifest aggregates all artifact hashes, reducing lookup complexity.
    SEED: Complete provenance from source to mint.

    Args:
        audio_id: Source audio identifier
        audio_hash: SHA256 hash of source audio
        symbolic_profile: SymbolicAudioProfile instance
        visual_artifact: VisualArtifact instance
        title: Asset title
        description: Asset description
        creator: Creator identifier
        collection_id: Optional collection identifier

    Returns:
        Complete MintManifest instance
    """
    from phonomicon.core.schemas import MintManifest

    # Compute hashes
    profile_hash = compute_hash(symbolic_profile)
    artifact_hash = visual_artifact.artifact_hash or compute_hash(visual_artifact)

    # Build provenance chain
    provenance = {
        "audio": {
            "audio_id": audio_id,
            "audio_hash": audio_hash,
        },
        "symbolic_profile": {
            "hash": profile_hash,
            "extraction_seed": symbolic_profile.extraction_seed,
            "model_version": symbolic_profile.model_version,
            "extracted_at": symbolic_profile.extracted_at.isoformat(),
        },
        "visual_artifact": {
            "artifact_id": visual_artifact.artifact_id,
            "hash": artifact_hash,
            "rendering_seed": visual_artifact.rendering_seed,
            "renderer_version": visual_artifact.renderer_version,
            "rendered_at": visual_artifact.rendered_at.isoformat(),
        },
    }

    # Combine traits from profile and artifact
    traits = {
        "runes": symbolic_profile.runes,
        "mythic_axis": symbolic_profile.mythic_axis,
        "archetype_tags": symbolic_profile.archetype_tags,
        **visual_artifact.traits,
    }

    # Generate manifest ID
    manifest_id = f"mint_{audio_id}_{int(datetime.utcnow().timestamp())}"

    manifest = MintManifest(
        manifest_id=manifest_id,
        audio_id=audio_id,
        audio_hash=audio_hash,
        symbolic_profile_hash=profile_hash,
        visual_artifact_id=visual_artifact.artifact_id,
        visual_artifact_hash=artifact_hash,
        title=title,
        description=description,
        creator=creator,
        runes=symbolic_profile.runes,
        mythic_axis=symbolic_profile.mythic_axis,
        archetype_tags=symbolic_profile.archetype_tags,
        traits=traits,
        collection_id=collection_id,
        provenance=provenance,
    )

    return manifest


def verify_provenance_chain(manifest: "MintManifest") -> bool:  # type: ignore
    """
    Verify the integrity of a provenance chain in a manifest.

    ABX-Core: Verification reduces trust requirements (cryptographic proof).

    Args:
        manifest: MintManifest to verify

    Returns:
        True if provenance chain is valid, False otherwise

    Note:
        This is a basic verification. In production, you would:
        - Verify each hash against actual artifacts
        - Check digital signatures
        - Validate timestamps
        - Ensure no hash collisions
    """
    # Basic validation: check that all required provenance fields exist
    required_keys = ["audio", "symbolic_profile", "visual_artifact"]

    if not all(key in manifest.provenance for key in required_keys):
        return False

    # Verify that manifest hashes match provenance hashes
    if manifest.symbolic_profile_hash != manifest.provenance["symbolic_profile"]["hash"]:
        return False

    if manifest.visual_artifact_hash != manifest.provenance["visual_artifact"]["hash"]:
        return False

    if manifest.audio_hash != manifest.provenance["audio"]["audio_hash"]:
        return False

    return True
