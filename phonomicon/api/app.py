"""
FastAPI application for Phonomicon.

ABX-Core: RESTful API provides standardized interface, reducing integration complexity.
SEED: All endpoints return traceable, deterministic responses.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from phonomicon import __version__
from phonomicon.config import get_settings
from phonomicon.core.schemas import (
    MintManifest,
    ResonanceFrame,
    SymbolicAudioProfile,
    VisualArtifact,
    VisualStyle,
)
from phonomicon.infra import BusClient, ERSScheduler
from phonomicon.services import analyze_audio, mint_asset, render_visual

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances (initialized in lifespan)
scheduler: Optional[ERSScheduler] = None
bus_client: Optional[BusClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    ABX-Core: Explicit resource lifecycle reduces state management complexity.
    """
    global scheduler, bus_client

    settings = get_settings()
    logger.info(f"Starting Phonomicon v{__version__} in {settings.environment} mode")

    # Initialize scheduler
    scheduler = ERSScheduler()
    await scheduler.start()
    logger.info("ERS Scheduler started")

    # Initialize bus client (optional - only if aal-core is available)
    try:
        bus_client = BusClient()
        await bus_client.connect()
        logger.info("Connected to aal-core message bus")
    except Exception as e:
        logger.warning(f"Could not connect to aal-core bus: {e}. Running in standalone mode.")
        bus_client = None

    yield

    # Cleanup
    if scheduler:
        await scheduler.stop()
        logger.info("ERS Scheduler stopped")

    if bus_client:
        await bus_client.disconnect()
        logger.info("Disconnected from aal-core message bus")


# Create FastAPI app
app = FastAPI(
    title="Phonomicon API",
    description="Sound-to-Art Minting Platform for Applied Alchemy Labs",
    version=__version__,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure based on environment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health and Status Endpoints
# ============================================================================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    scheduler_running: bool = Field(..., description="Scheduler status")
    bus_connected: bool = Field(..., description="Bus connection status")


@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Health check endpoint.

    ABX-Core: Explicit health reporting reduces operational ambiguity.
    """
    scheduler_running = scheduler is not None and scheduler._running
    bus_connected = bus_client is not None and bus_client._connected

    return HealthResponse(
        status="healthy" if scheduler_running else "degraded",
        version=__version__,
        scheduler_running=scheduler_running,
        bus_connected=bus_connected,
    )


# ============================================================================
# Audio Analysis Endpoint
# ============================================================================


class AnalyzeAudioRequest(BaseModel):
    """Request model for audio analysis."""

    resonance_frame: ResonanceFrame = Field(..., description="Input ResonanceFrame")
    seed: Optional[int] = Field(None, description="Optional seed for deterministic analysis")


class AnalyzeAudioResponse(BaseModel):
    """Response model for audio analysis."""

    symbolic_profile: SymbolicAudioProfile = Field(..., description="Extracted profile")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")


@app.post(
    "/analyze-audio",
    response_model=AnalyzeAudioResponse,
    status_code=status.HTTP_200_OK,
    tags=["Analysis"],
)
async def api_analyze_audio(request: AnalyzeAudioRequest):
    """
    Analyze audio and extract symbolic profile.

    SEED: Deterministic analysis with optional seed parameter.

    Args:
        request: Analysis request with ResonanceFrame

    Returns:
        Symbolic audio profile

    Raises:
        400: If ResonanceFrame is invalid
        500: If analysis fails
    """
    try:
        import time

        start = time.time()

        # Perform analysis
        profile = await analyze_audio(request.resonance_frame, seed=request.seed)

        processing_time = (time.time() - start) * 1000

        # Emit event to bus if connected
        if bus_client:
            await bus_client.emit_event(
                "analysis.completed",
                {
                    "audio_id": profile.audio_id,
                    "runes": profile.runes,
                    "mythic_axis": profile.mythic_axis,
                },
            )

        return AnalyzeAudioResponse(
            symbolic_profile=profile, processing_time_ms=processing_time
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Audio analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Audio analysis failed",
        )


# ============================================================================
# Visual Rendering Endpoint
# ============================================================================


class RenderVisualRequest(BaseModel):
    """Request model for visual rendering."""

    symbolic_profile: SymbolicAudioProfile = Field(..., description="Input profile")
    style: VisualStyle = Field(
        default=VisualStyle.GENERATIVE, description="Rendering style"
    )
    dimensions: tuple[int, int] = Field(
        default=(1024, 1024), description="Output dimensions (width, height)"
    )
    seed: Optional[int] = Field(None, description="Optional seed for deterministic rendering")


class RenderVisualResponse(BaseModel):
    """Response model for visual rendering."""

    visual_artifact: VisualArtifact = Field(..., description="Rendered artifact")
    processing_time_ms: Optional[float] = Field(None, description="Processing time")


@app.post(
    "/render-visual",
    response_model=RenderVisualResponse,
    status_code=status.HTTP_200_OK,
    tags=["Rendering"],
)
async def api_render_visual(request: RenderVisualRequest):
    """
    Render visual artifact from symbolic profile.

    SEED: Deterministic rendering with optional seed parameter.

    Args:
        request: Rendering request with SymbolicAudioProfile

    Returns:
        Visual artifact metadata

    Raises:
        400: If profile is invalid
        500: If rendering fails
    """
    try:
        import time

        start = time.time()

        # Perform rendering
        artifact = await render_visual(
            request.symbolic_profile,
            style=request.style,
            dimensions=request.dimensions,
            seed=request.seed,
        )

        processing_time = (time.time() - start) * 1000

        # Emit event to bus if connected
        if bus_client:
            await bus_client.emit_event(
                "visual.rendered",
                {
                    "artifact_id": artifact.artifact_id,
                    "source_audio_id": artifact.source_audio_id,
                    "style": artifact.style.value,
                },
            )

        return RenderVisualResponse(
            visual_artifact=artifact, processing_time_ms=processing_time
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Visual rendering failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Visual rendering failed",
        )


# ============================================================================
# Asset Minting Endpoint
# ============================================================================


class MintAssetRequest(BaseModel):
    """Request model for asset minting."""

    audio_id: str = Field(..., description="Source audio identifier")
    audio_hash: str = Field(..., description="SHA256 hash of source audio")
    symbolic_profile: SymbolicAudioProfile = Field(..., description="Symbolic profile")
    visual_artifact: VisualArtifact = Field(..., description="Visual artifact")
    title: str = Field(..., description="Asset title")
    description: str = Field(..., description="Asset description")
    creator: str = Field(..., description="Creator identifier")
    collection_id: Optional[str] = Field(None, description="Optional collection ID")
    chain: Optional[str] = Field(None, description="Optional blockchain identifier")


class MintAssetResponse(BaseModel):
    """Response model for asset minting."""

    manifest: MintManifest = Field(..., description="Mint manifest")
    verified: bool = Field(..., description="Provenance verification status")
    transaction_hash: Optional[str] = Field(None, description="On-chain transaction hash")
    token_id: Optional[str] = Field(None, description="Token ID")


@app.post(
    "/mint-asset",
    response_model=MintAssetResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Minting"],
)
async def api_mint_asset(request: MintAssetRequest):
    """
    Mint an asset with complete provenance.

    SEED: Verifies provenance chain before minting.

    Args:
        request: Minting request with all asset components

    Returns:
        Mint manifest and receipt

    Raises:
        400: If inputs are invalid or provenance fails
        500: If minting fails
    """
    try:
        # Perform minting
        receipt = await mint_asset(
            audio_id=request.audio_id,
            audio_hash=request.audio_hash,
            symbolic_profile=request.symbolic_profile,
            visual_artifact=request.visual_artifact,
            title=request.title,
            description=request.description,
            creator=request.creator,
            collection_id=request.collection_id,
            chain=request.chain,
        )

        if not receipt.verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provenance verification failed: {receipt.error}",
            )

        # Emit event to bus if connected
        if bus_client:
            await bus_client.emit_event(
                "mint.completed",
                {
                    "manifest_id": receipt.manifest.manifest_id,
                    "audio_id": receipt.manifest.audio_id,
                    "creator": receipt.manifest.creator,
                },
                priority="high",
            )

        return MintAssetResponse(
            manifest=receipt.manifest,
            verified=receipt.verified,
            transaction_hash=receipt.transaction_hash,
            token_id=receipt.token_id,
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Asset minting failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Asset minting failed"
        )


# ============================================================================
# Utility Endpoints
# ============================================================================


@app.get("/scheduler/stats", tags=["System"])
async def scheduler_stats():
    """Get scheduler statistics."""
    if not scheduler:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Scheduler not available"
        )

    return {
        "running": scheduler._running,
        "queue_size": scheduler.get_queue_size(),
        "max_workers": scheduler.max_workers,
        "gpu_enabled": scheduler.gpu_enabled,
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "phonomicon.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug_mode,
        log_level=settings.log_level.lower(),
    )
