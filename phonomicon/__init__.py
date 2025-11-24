"""
Phonomicon: Sound-to-Art Minting Platform

Part of Applied Alchemy Labs (AAL) ecosystem.
Implements ABX-Core v1.2 and SEED Framework principles.
"""

__version__ = "0.1.0"

from phonomicon.core.schemas import (
    ResonanceFrame,
    SymbolicAudioProfile,
    VisualArtifact,
    MintManifest,
)
from phonomicon.services.analytics import analyze_audio
from phonomicon.services.mint import mint_asset
from phonomicon.services.visual import render_visual

__all__ = [
    "ResonanceFrame",
    "SymbolicAudioProfile",
    "VisualArtifact",
    "MintManifest",
    "analyze_audio",
    "render_visual",
    "mint_asset",
]
