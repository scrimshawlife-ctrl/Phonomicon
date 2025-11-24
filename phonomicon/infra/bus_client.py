"""
Message bus client for aal-core integration.

ABX-Core: Centralized messaging reduces inter-module coupling (entropy).
SEED: All messages are typed and traceable.
"""

import logging
from typing import Any, Callable, Optional

import httpx

from phonomicon.config import get_settings
from phonomicon.core.schemas import ResonanceFrame

logger = logging.getLogger(__name__)


class BusClient:
    """
    Client for aal-core message bus.

    ABX-Core: Standardized messaging protocol reduces integration complexity.

    This client provides:
    - Publishing messages to the bus
    - Subscribing to message topics
    - Sending ResonanceFrames to other modules
    - Receiving events from aal-core

    Note:
        This is a scaffold implementation. Real implementation would:
        - Use WebSocket for bidirectional messaging
        - Implement reconnection logic with exponential backoff
        - Handle message serialization/deserialization
        - Support message acknowledgment and retries
        - Integrate with aal-core's actual message bus protocol
    """

    def __init__(self, bus_url: str | None = None):
        """
        Initialize bus client.

        Args:
            bus_url: URL of aal-core message bus (defaults to config)
        """
        settings = get_settings()
        self.bus_url = bus_url or settings.aal_message_bus_url
        self.module_name = "phonomicon"

        # HTTP client for REST-based messaging (TODO: replace with WebSocket)
        self._client: Optional[httpx.AsyncClient] = None
        self._connected = False

        logger.info(f"BusClient initialized: bus_url={self.bus_url}")

    async def connect(self) -> None:
        """
        Connect to aal-core message bus.

        ABX-Core: Explicit connection lifecycle reduces state ambiguity.
        """
        if self._connected:
            logger.warning("BusClient already connected")
            return

        self._client = httpx.AsyncClient(base_url=self.bus_url, timeout=30.0)

        # TODO: Implement real connection handshake
        # - WebSocket upgrade
        # - Authentication
        # - Module registration with aal-core

        self._connected = True
        logger.info("BusClient connected to aal-core")

    async def disconnect(self) -> None:
        """Disconnect from message bus."""
        if not self._connected:
            return

        if self._client:
            await self._client.aclose()
            self._client = None

        self._connected = False
        logger.info("BusClient disconnected")

    async def publish(
        self, topic: str, message: dict[str, Any], priority: str = "normal"
    ) -> None:
        """
        Publish a message to the bus.

        ABX-Core: Topic-based routing reduces message delivery ambiguity.

        Args:
            topic: Message topic (e.g., "phonomicon.analysis.complete")
            message: Message payload (must be JSON-serializable)
            priority: Message priority ("low", "normal", "high", "critical")

        Raises:
            RuntimeError: If not connected to bus
        """
        if not self._connected or not self._client:
            raise RuntimeError("Not connected to message bus. Call connect() first.")

        payload = {
            "topic": topic,
            "source": self.module_name,
            "priority": priority,
            "message": message,
        }

        # TODO: Implement real message publishing
        # For now, just log (would POST to /bus/publish in real implementation)
        logger.debug(f"Publishing to topic '{topic}': {message}")

        try:
            # Placeholder HTTP POST
            # response = await self._client.post("/publish", json=payload)
            # response.raise_for_status()
            pass
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
            raise

    async def send_resonance_frame(self, frame: ResonanceFrame, target_module: str) -> None:
        """
        Send a ResonanceFrame to another module via the bus.

        SEED: ResonanceFrame provides standard inter-module data format.

        Args:
            frame: ResonanceFrame to send
            target_module: Target module name (e.g., "abraxas", "noctis")

        Raises:
            RuntimeError: If not connected to bus
        """
        if not self._connected:
            raise RuntimeError("Not connected to message bus. Call connect() first.")

        # Serialize frame to dict
        frame_data = frame.model_dump(mode="json")

        # Publish to module-specific topic
        topic = f"{target_module}.resonance_frame"
        await self.publish(topic, frame_data, priority="normal")

        logger.debug(f"Sent ResonanceFrame {frame.frame_id} to {target_module}")

    async def subscribe(
        self, topic: str, callback: Callable[[dict[str, Any]], None]
    ) -> None:
        """
        Subscribe to a message topic.

        Args:
            topic: Topic pattern to subscribe to (supports wildcards in real impl)
            callback: Async callback function to handle messages

        Raises:
            RuntimeError: If not connected to bus

        Note:
            TODO: Implement real subscription mechanism.
            Would typically:
            - Register subscription with aal-core
            - Set up WebSocket listener
            - Route incoming messages to callback
            - Handle reconnection and re-subscription
        """
        if not self._connected:
            raise RuntimeError("Not connected to message bus. Call connect() first.")

        # TODO: Implement real subscription
        logger.info(f"Subscribed to topic: {topic}")

    async def emit_event(
        self, event_type: str, data: dict[str, Any], priority: str = "normal"
    ) -> None:
        """
        Emit a Phonomicon event to the bus.

        Common event types:
        - phonomicon.analysis.started
        - phonomicon.analysis.completed
        - phonomicon.visual.rendered
        - phonomicon.mint.requested
        - phonomicon.mint.completed

        Args:
            event_type: Event type identifier
            data: Event data
            priority: Event priority
        """
        topic = f"phonomicon.events.{event_type}"
        await self.publish(topic, data, priority)

    async def health_check(self) -> bool:
        """
        Check if connection to bus is healthy.

        Returns:
            True if healthy, False otherwise
        """
        if not self._connected or not self._client:
            return False

        try:
            # TODO: Implement real health check (e.g., ping endpoint)
            # response = await self._client.get("/health")
            # return response.status_code == 200
            return True
        except Exception as e:
            logger.error(f"Bus health check failed: {e}")
            return False
