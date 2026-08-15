"""
Event-Driven System Integration Module

This module provides the main integration point for enabling event-driven
execution in Retinue. It handles initialization, startup, and provides
backwards compatibility with the existing polling-based system.
"""

import asyncio
import logging
from typing import Optional

from app.core.config import settings
from app.services.event_bus import initialize_event_bus, shutdown_event_bus, get_event_bus
from app.services.db_event_publisher import register_db_event_listeners
from app.services.dependency_resolver import start_dependency_resolution
from app.agents.hr_monitoring_service import start_hr_monitoring, stop_hr_monitoring

logger = logging.getLogger(__name__)


class EventDrivenSystemManager:
    """
    Manages the event-driven execution system.

    Handles:
    - System initialization and shutdown
    - Mode switching (event_driven, hybrid, polling)
    - Service lifecycle management
    """

    def __init__(self):
        self.mode = settings.AGENT_EXECUTION_MODE
        self.initialized = False
        self.services_started = False

    async def initialize(self):
        """
        Initialize the event-driven system.

        This should be called during application startup.
        """
        if self.initialized:
            logger.warning("Event-driven system already initialized")
            return

        logger.info(f"🚀 Initializing event-driven system (mode: {self.mode})")

        if self.mode in ["event_driven", "hybrid"]:
            # Initialize event bus
            await initialize_event_bus(
                backend=settings.EVENT_BUS_BACKEND,
                redis_url=settings.REDIS_URL if settings.EVENT_BUS_BACKEND == "redis" else None,
            )

            logger.info("✅ Event bus initialized")

        self.initialized = True
        logger.info(f"✅ Event-driven system initialized in {self.mode} mode")

    async def start_services(self):
        """
        Start all event-driven services.

        This should be called after all agents are initialized.
        """
        if not self.initialized:
            raise RuntimeError("System not initialized. Call initialize() first.")

        if self.services_started:
            logger.warning("Event-driven services already started")
            return

        logger.info("🔧 Starting event-driven services...")

        if self.mode in ["event_driven", "hybrid"]:
            # Register database event listeners for automatic event publishing
            register_db_event_listeners()
            logger.info("✅ Database event listeners registered")

            # Start dependency resolver
            start_dependency_resolution()
            logger.info("✅ Dependency resolver started")

            # Start HR monitoring service
            if settings.HR_MONITORING_ENABLED:
                await start_hr_monitoring()
                logger.info("✅ HR monitoring service started")

        self.services_started = True
        logger.info("✅ All event-driven services started")

    async def shutdown(self):
        """
        Shutdown the event-driven system gracefully.

        This should be called during application shutdown.
        """
        logger.info("🛑 Shutting down event-driven system...")

        if self.mode in ["event_driven", "hybrid"]:
            # Stop HR monitoring
            if settings.HR_MONITORING_ENABLED:
                await stop_hr_monitoring()
                logger.info("✅ HR monitoring stopped")

            # Shutdown event bus
            await shutdown_event_bus()
            logger.info("✅ Event bus shutdown")

        self.initialized = False
        self.services_started = False
        logger.info("✅ Event-driven system shutdown complete")

    def get_mode(self) -> str:
        """Get current execution mode"""
        return self.mode

    def is_event_driven(self) -> bool:
        """Check if running in event-driven mode"""
        return self.mode == "event_driven"

    def is_hybrid(self) -> bool:
        """Check if running in hybrid mode"""
        return self.mode == "hybrid"

    def is_polling(self) -> bool:
        """Check if running in legacy polling mode"""
        return self.mode == "polling"


# Global instance
_system_manager: Optional[EventDrivenSystemManager] = None


def get_system_manager() -> EventDrivenSystemManager:
    """Get the global system manager instance"""
    global _system_manager
    if _system_manager is None:
        _system_manager = EventDrivenSystemManager()
    return _system_manager


async def initialize_event_driven_system():
    """
    Initialize the event-driven system (convenience function).

    Call this during application startup.
    """
    manager = get_system_manager()
    await manager.initialize()


async def start_event_driven_services():
    """
    Start all event-driven services (convenience function).

    Call this after all agents are initialized.
    """
    manager = get_system_manager()
    await manager.start_services()


async def shutdown_event_driven_system():
    """
    Shutdown the event-driven system (convenience function).

    Call this during application shutdown.
    """
    manager = get_system_manager()
    await manager.shutdown()


def get_execution_mode() -> str:
    """Get the current execution mode"""
    manager = get_system_manager()
    return manager.get_mode()


def is_event_driven_mode() -> bool:
    """Check if running in event-driven mode"""
    manager = get_system_manager()
    return manager.is_event_driven()


# ============================================================================
# AGENT STARTUP HELPER FUNCTIONS
# ============================================================================

async def start_agent_event_driven(agent):
    """
    Start an agent in event-driven mode.

    Args:
        agent: Agent instance (must have EventDrivenMixin)

    Example:
        from app.agents.ceo_agent import CEOAgent
        from app.services.event_driven_integration import start_agent_event_driven

        ceo = CEOAgent()
        await start_agent_event_driven(ceo)
    """
    if not hasattr(agent, "start_event_driven_mode"):
        raise TypeError(
            f"Agent {agent.name} does not have EventDrivenMixin. "
            f"Add EventDrivenMixin to agent class."
        )

    await agent.start_event_driven_mode()
    logger.info(f"✅ {agent.name} started in event-driven mode")


async def start_agent_hybrid(agent):
    """
    Start an agent in hybrid mode (event-driven + periodic health checks).

    Args:
        agent: Agent instance (must have EventDrivenMixin)
    """
    if not hasattr(agent, "run_hybrid_mode"):
        raise TypeError(
            f"Agent {agent.name} does not have EventDrivenMixin. "
            f"Add EventDrivenMixin to agent class."
        )

    # Run hybrid mode (this will block, so run in background)
    asyncio.create_task(agent.run_hybrid_mode())
    logger.info(f"✅ {agent.name} started in hybrid mode")


async def start_agent_polling(agent):
    """
    Start an agent in legacy polling mode.

    Args:
        agent: Agent instance

    Example:
        from app.agents.ceo_agent import CEOAgent
        from app.services.event_driven_integration import start_agent_polling

        ceo = CEOAgent()
        await start_agent_polling(ceo)
    """
    # Run polling mode (this will block, so run in background)
    asyncio.create_task(agent.start())
    logger.info(f"✅ {agent.name} started in polling mode")


async def start_agent(agent):
    """
    Start an agent using the configured execution mode.

    This function automatically selects the appropriate startup method
    based on settings.AGENT_EXECUTION_MODE.

    Args:
        agent: Agent instance

    Example:
        from app.agents.ceo_agent import CEOAgent
        from app.services.event_driven_integration import start_agent

        ceo = CEOAgent()
        await start_agent(ceo)  # Automatically uses configured mode
    """
    manager = get_system_manager()

    if manager.is_event_driven():
        await start_agent_event_driven(agent)
    elif manager.is_hybrid():
        await start_agent_hybrid(agent)
    else:  # polling
        await start_agent_polling(agent)


# ============================================================================
# BACKWARDS COMPATIBILITY HELPERS
# ============================================================================

class BackwardsCompatibilityWrapper:
    """
    Wrapper that provides backwards compatibility for agents that
    don't yet have EventDrivenMixin.

    This allows gradual migration to event-driven mode.
    """

    def __init__(self, agent):
        self.agent = agent
        self.event_bus = get_event_bus()

    async def simulate_event_driven(self):
        """
        Simulate event-driven behavior for legacy agents.

        Polls for work but at a much faster rate (every 10 seconds)
        and subscribes to basic events.
        """
        logger.info(
            f"⚠️ {self.agent.name}: Running in compatibility mode "
            f"(faster polling + basic events)"
        )

        # Subscribe to high-priority events
        self.event_bus.subscribe_agent(
            agent_id=self.agent.agent_id,
            callback=self._on_high_priority_event,
        )

        # Run faster polling (10 seconds instead of 15 minutes)
        while True:
            try:
                await self.agent.check_cycle()
            except Exception as e:
                logger.error(f"Error in {self.agent.name} check cycle: {e}")

            await asyncio.sleep(10)  # 10 seconds instead of 900

    async def _on_high_priority_event(self, event):
        """Handle high-priority events"""
        logger.info(
            f"{self.agent.name}: Received high-priority event "
            f"{event.event_type.value}, triggering immediate check"
        )

        # Trigger immediate check cycle
        try:
            await self.agent.check_cycle()
        except Exception as e:
            logger.error(f"Error in immediate check: {e}")


async def start_agent_with_compatibility(agent):
    """
    Start an agent with backwards compatibility.

    If agent has EventDrivenMixin, uses event-driven mode.
    Otherwise, uses compatibility mode with faster polling.

    Args:
        agent: Agent instance
    """
    if hasattr(agent, "start_event_driven_mode"):
        # Agent supports event-driven mode
        await start_agent(agent)
    else:
        # Agent doesn't support event-driven, use compatibility mode
        wrapper = BackwardsCompatibilityWrapper(agent)
        asyncio.create_task(wrapper.simulate_event_driven())
        logger.info(
            f"✅ {agent.name} started with backwards compatibility "
            f"(faster polling + basic events)"
        )
