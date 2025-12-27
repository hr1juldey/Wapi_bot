"""LLM warmup service - keeps Ollama model warm and ready.

Prevents cold-start delays by:
1. Startup warmup: Ask 3-5 basic questions on server start
2. Idle warmup: Ask 1 question after configured idle time
"""

import asyncio
import logging

import random
from pathlib import Path
from typing import Optional
from datetime import datetime

from core.config import settings

logger = logging.getLogger(__name__)

# Persist warmup timestamp to survive hot reloads
WARMUP_STATE_FILE = Path("/tmp/.wapibot_warmup_state")


class WarmupService:
    """Intelligent LLM warmup to avoid cold-start delays."""

    # Basic warmup prompt templates (will be randomized to bypass cache)
    STARTUP_PROMPT_TEMPLATES = [
        "My name is Test User",
        "I have a Honda City",
        "My number is 9876543210",
        "Book for tomorrow",
        "Thanks!"
    ]

    IDLE_PROMPT_TEMPLATE = "My name is Warmup Check"

    @staticmethod
    def _randomize_prompt(prompt: str) -> str:
        """Add randomness to prompt to prevent DSPy cache hits.

        Args:
            prompt: Base prompt template

        Returns:
            Prompt with timestamp and random number to bypass cache
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_num = random.randint(1000, 9999)
        return f"{prompt} [{timestamp}_{random_num}]"

    def __init__(self):
        self.last_activity = datetime.now()
        self.last_warmup = self._load_last_warmup()  # Load from file (survives hot reload)
        self.warmup_in_progress = False

        # Load config values (no magic numbers!)
        self.warmup_cooldown = settings.warmup_cooldown_seconds
        self.idle_threshold = settings.warmup_idle_threshold_seconds
        self.check_interval = settings.warmup_idle_check_interval
        self.warmup_timeout = settings.extraction_timeout_warmup
        self.idle_timeout = settings.extraction_timeout_normal

    def _load_last_warmup(self) -> Optional[datetime]:
        """Load last warmup timestamp from file (survives hot reload)."""
        try:
            if WARMUP_STATE_FILE.exists():
                timestamp_str = WARMUP_STATE_FILE.read_text().strip()
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.debug(f"Failed to load warmup state: {e}")
        return None

    def _save_last_warmup(self, timestamp: datetime) -> None:
        """Save last warmup timestamp to file."""
        try:
            WARMUP_STATE_FILE.write_text(timestamp.isoformat())
        except Exception as e:
            logger.debug(f"Failed to save warmup state: {e}")

    async def startup_warmup(self) -> None:
        """
        Run on server startup to warm up the LLM.

        Asks 3-5 basic questions to:
        - Load model into memory
        - Prime KV cache
        - Reduce first real request latency from 30-90s to <5s

        Skips if warmup happened within 300s (prevents hot reload spam).
        """
        # Skip if warmup already in progress
        if self.warmup_in_progress:
            logger.info("⏭️  Warmup already in progress, skipping")
            return

        # Skip if warmup happened recently (hot reload protection)
        if self.last_warmup:
            seconds_since_warmup = (datetime.now() - self.last_warmup).total_seconds()
            if seconds_since_warmup < self.warmup_cooldown:
                logger.info(
                    f"⏭️  Warmup done {seconds_since_warmup:.0f}s ago "
                    f"(< {self.warmup_cooldown}s cooldown), skipping"
                )
                return

        self.warmup_in_progress = True
        logger.info("🔥 Starting LLM warmup (startup)...")

        try:
            # Import here to avoid circular dependency
            from dspy_modules.extractors.name_extractor import NameExtractor
            extractor = NameExtractor()

            # Run warmup questions sequentially
            for i, prompt_template in enumerate(self.STARTUP_PROMPT_TEMPLATES, 1):
                try:
                    # Randomize prompt to bypass DSPy cache
                    prompt = self._randomize_prompt(prompt_template)
                    logger.info(f"🔥 Warmup {i}/{len(self.STARTUP_PROMPT_TEMPLATES)}: {prompt_template[:30]}...")

                    # Run in executor (DSPy is sync)
                    loop = asyncio.get_event_loop()
                    await asyncio.wait_for(
                        loop.run_in_executor(
                            None,
                            lambda p=prompt: extractor(
                                conversation_history=[],
                                user_message=p,
                                context="Warmup query"
                            )
                        ),
                        timeout=self.warmup_timeout  # From config (hardware dependent)
                    )
                    #logger.info(f"✅ Warmup {i} complete")

                except asyncio.TimeoutError:
                    logger.warning(f"⏱️  Warmup {i} timed out (model still loading?)")
                except Exception as e:
                    logger.warning(f"⚠️  Warmup {i} failed: {e}")
                    # Continue with next prompt
                    continue

            logger.info("✅ LLM warmup complete - model is warm and ready!")
            now = datetime.now()
            self.last_warmup = now
            self._save_last_warmup(now)  # Persist to file (survives hot reload)

        except Exception as e:
            logger.error(f"❌ Warmup failed: {e}")

        finally:
            self.warmup_in_progress = False
            self.update_activity()

    async def idle_warmup(self) -> None:
        """
        Quick warmup after idle period.

        Asks just 1 question to keep model loaded.
        Prevents model from unloading due to OLLAMA_KEEP_ALIVE.
        """
        if self.warmup_in_progress:
            return

        self.warmup_in_progress = True
        logger.info("🔥 Idle warmup triggered (keeping model warm)...")

        try:
            from dspy_modules.extractors.name_extractor import NameExtractor
            extractor = NameExtractor()

            # Randomize prompt to bypass DSPy cache
            prompt = self._randomize_prompt(self.IDLE_PROMPT_TEMPLATE)

            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: extractor(
                        conversation_history=[],
                        user_message=prompt,
                        context="Idle warmup"
                    )
                ),
                timeout=self.idle_timeout  # From config
            )
            logger.info("✅ Idle warmup complete")
            now = datetime.now()
            self.last_warmup = now
            self._save_last_warmup(now)  # Persist to file (survives hot reload)

        except Exception as e:
            logger.warning(f"⚠️  Idle warmup failed: {e}")

        finally:
            self.warmup_in_progress = False
            self.update_activity()

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now()

    def seconds_since_activity(self) -> float:
        """Get seconds since last activity."""
        return (datetime.now() - self.last_activity).total_seconds()

    async def start_idle_monitor(self, idle_threshold: int | None = None) -> None:
        """
        Background task to monitor idle time and trigger warmup.

        Args:
            idle_threshold: Seconds of idle time before warmup (default: from config)
        """
        # Use parameter or fall back to config
        threshold = idle_threshold if idle_threshold is not None else self.idle_threshold

        logger.info(f"🔍 Starting idle monitor (threshold: {threshold}s)")

        while True:
            try:
                await asyncio.sleep(self.check_interval)  # From config

                idle_time = self.seconds_since_activity()
                if idle_time >= threshold:
                    logger.info(f"⏰ Idle for {idle_time:.0f}s, triggering warmup...")
                    await self.idle_warmup()

            except Exception as e:
                logger.error(f"❌ Idle monitor error: {e}")
                await asyncio.sleep(self.check_interval)  # From config


# Global instance
warmup_service = WarmupService()