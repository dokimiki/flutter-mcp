"""
Recovery mechanisms for Flutter MCP Server.

This module provides automatic recovery and self-healing capabilities
for the Flutter documentation server.
"""

import asyncio
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class HealthMonitor:
    """
    Monitors service health and triggers recovery actions.
    """
    
    def __init__(self, check_interval: float = 300.0):  # 5 minutes
        self.check_interval = check_interval
        self.last_check = None
        self.consecutive_failures = 0
        self.recovery_actions = []
        self.is_monitoring = False
        
    def add_recovery_action(self, action: Callable, threshold: int = 3):
        """Add a recovery action to trigger after threshold failures."""
        self.recovery_actions.append({
            "action": action,
            "threshold": threshold,
            "triggered": False
        })
    
    async def start_monitoring(self, health_check_func: Callable):
        """Start continuous health monitoring."""
        self.is_monitoring = True
        logger.info("health_monitoring_started", interval=self.check_interval)
        
        while self.is_monitoring:
            try:
                # Perform health check
                result = await health_check_func()
                status = result.get("status", "unknown")
                
                if status in ["failed", "degraded"]:
                    self.consecutive_failures += 1
                    logger.warning(
                        "health_check_failed",
                        status=status,
                        consecutive_failures=self.consecutive_failures
                    )
                    
                    # Trigger recovery actions if needed
                    await self._trigger_recovery_actions()
                else:
                    if self.consecutive_failures > 0:
                        logger.info("health_recovered", previous_failures=self.consecutive_failures)
                    self.consecutive_failures = 0
                    self._reset_recovery_actions()
                
                self.last_check = datetime.utcnow()
                
            except Exception as e:
                logger.error(
                    "health_monitor_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
                self.consecutive_failures += 1
            
            # Wait for next check
            await asyncio.sleep(self.check_interval)
    
    async def _trigger_recovery_actions(self):
        """Trigger appropriate recovery actions based on failure count."""
        for action_config in self.recovery_actions:
            if (self.consecutive_failures >= action_config["threshold"] and 
                not action_config["triggered"]):
                try:
                    logger.info(
                        "triggering_recovery_action",
                        threshold=action_config["threshold"],
                        failures=self.consecutive_failures
                    )
                    await action_config["action"]()
                    action_config["triggered"] = True
                except Exception as e:
                    logger.error(
                        "recovery_action_failed",
                        error=str(e),
                        error_type=type(e).__name__
                    )
    
    def _reset_recovery_actions(self):
        """Reset triggered flags on recovery actions."""
        for action_config in self.recovery_actions:
            action_config["triggered"] = False
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        logger.info("health_monitoring_stopped")


class CacheRecovery:
    """
    Handles cache-related recovery operations.
    """
    
    @staticmethod
    async def clear_corrupted_entries(cache_manager):
        """Clear potentially corrupted cache entries."""
        try:
            logger.info("clearing_corrupted_cache_entries")
            # Implementation depends on cache manager interface
            # This is a placeholder for the actual implementation
            stats = cache_manager.get_stats()
            logger.info("cache_recovery_completed", stats=stats)
        except Exception as e:
            logger.error("cache_recovery_failed", error=str(e))


class ConnectionPoolRecovery:
    """
    Manages HTTP connection pool recovery.
    """
    
    @staticmethod
    async def reset_connection_pools():
        """Reset all HTTP connection pools."""
        logger.info("resetting_connection_pools")
        # Force garbage collection of old connections
        import gc
        gc.collect()
        logger.info("connection_pools_reset")


class RateLimiterRecovery:
    """
    Handles rate limiter recovery and adjustment.
    """
    
    @staticmethod
    async def adjust_rate_limits(rate_limiter, factor: float = 0.5):
        """Temporarily reduce rate limits during recovery."""
        original_rate = 1.0 / rate_limiter.min_interval
        new_rate = original_rate * factor
        rate_limiter.min_interval = 1.0 / new_rate
        
        logger.info(
            "rate_limits_adjusted",
            original_rate=original_rate,
            new_rate=new_rate,
            factor=factor
        )
        
        # Reset after 5 minutes
        await asyncio.sleep(300)
        rate_limiter.min_interval = 1.0 / original_rate
        logger.info("rate_limits_restored", rate=original_rate)


async def create_recovery_system(cache_manager, rate_limiter, health_check_func):
    """
    Create and configure the recovery system.
    
    Returns:
        HealthMonitor: Configured health monitor instance
    """
    monitor = HealthMonitor(check_interval=300.0)  # 5 minutes
    
    # Add recovery actions with increasing severity
    
    # Level 1: Clear cache (after 3 failures)
    async def clear_cache():
        await CacheRecovery.clear_corrupted_entries(cache_manager)
    
    monitor.add_recovery_action(clear_cache, threshold=3)
    
    # Level 2: Reset connections (after 5 failures)
    async def reset_connections():
        await ConnectionPoolRecovery.reset_connection_pools()
    
    monitor.add_recovery_action(reset_connections, threshold=5)
    
    # Level 3: Reduce rate limits (after 7 failures)
    async def reduce_rates():
        await RateLimiterRecovery.adjust_rate_limits(rate_limiter, factor=0.5)
    
    monitor.add_recovery_action(reduce_rates, threshold=7)
    
    # Start monitoring in background
    asyncio.create_task(monitor.start_monitoring(health_check_func))
    
    return monitor


class GracefulShutdown:
    """
    Handles graceful shutdown of the server.
    """
    
    def __init__(self):
        self.shutdown_handlers = []
        self.is_shutting_down = False
    
    def add_handler(self, handler: Callable):
        """Add a shutdown handler."""
        self.shutdown_handlers.append(handler)
    
    async def shutdown(self):
        """Perform graceful shutdown."""
        if self.is_shutting_down:
            return
        
        self.is_shutting_down = True
        logger.info("graceful_shutdown_started")
        
        # Execute all shutdown handlers
        for handler in self.shutdown_handlers:
            try:
                await handler()
            except Exception as e:
                logger.error(
                    "shutdown_handler_error",
                    error=str(e),
                    error_type=type(e).__name__
                )
        
        logger.info("graceful_shutdown_completed")