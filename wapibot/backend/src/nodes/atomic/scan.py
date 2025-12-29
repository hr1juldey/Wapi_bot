"""Atomic scan node - retroactively scan conversation history for missing data.

This single node can scan for ANY data using ANY extractor.
Configuration over specialization - V1's strength preserved in V2.

Usage:
    # Scan history for missing name
    scan.node(state, NameExtractor(), "customer.first_name", max_turns=10)

    # Scan history for missing phone (SAME node, different config!)
    scan.node(state, PhoneExtractor(), "customer.phone", max_turns=5)

    # Scan history for missing vehicle
    scan.node(state, VehicleExtractor(), "vehicle.brand", max_turns=10)
"""

import asyncio
import logging
from typing import Any, Optional, Protocol
from workflows.shared.state import BookingState
from core.config import settings

logger = logging.getLogger(__name__)


class Extractor(Protocol):
    """Protocol for extractors that can scan history."""

    def __call__(
        self,
        conversation_history: list,
        user_message: str,
        **kwargs
    ) -> dict[str, Any]:
        """Extract data from conversation."""
        ...


def get_nested_field(state: BookingState, field_path: str) -> Any:
    """Get nested field from state using dot notation."""
    parts = field_path.split(".")
    current = state

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_nested_field(state: BookingState, field_path: str, value: Any) -> None:
    """Set nested field in state using dot notation."""
    parts = field_path.split(".")
    current = state

    for part in parts[:-1]:
        if part not in current or current[part] is None:
            current[part] = {}
        current = current[part]

    current[parts[-1]] = value


async def node(
    state: BookingState,
    extractor: Extractor,
    field_path: str,
    max_turns: int = 10,
    skip_if_exists: bool = True,
    timeout: Optional[float] = None
) -> BookingState:
    """Atomic scan node - retroactively scan history for missing data.

    This implements V1's retroactive scanning strength - filling gaps from
    conversation history without overwriting existing high-confidence data.

    Args:
        state: Current booking state
        extractor: ANY extractor to scan history with
        field_path: Field to fill (e.g., "customer.first_name")
        max_turns: Maximum conversation turns to scan (default: 10)
        skip_if_exists: Skip scanning if field already exists (default: True)
        timeout: Extraction timeout per turn

    Returns:
        Updated state with scanned data

    Example:
        # User mentioned name 3 turns ago, but extraction failed
        # Now we retroactively scan to fill the gap
        state = await scan.node(
            state,
            NameExtractor(),
            "customer.first_name",
            max_turns=5
        )

        # Same node, different data!
        state = await scan.node(
            state,
            VehicleExtractor(),
            "vehicle.brand",
            max_turns=10
        )
    """
    # Check if field already exists
    current_value = get_nested_field(state, field_path)

    if skip_if_exists and current_value is not None:
        logger.info(f"⏭️ Skipping scan for {field_path} (already exists: {current_value})")
        return state

    logger.info(f"🔍 Scanning history for {field_path} (max {max_turns} turns)")

    # Get conversation history
    history = state.get("history", [])

    if not history:
        logger.warning(f"⚠️ No history to scan for {field_path}")
        return state

    # Scan recent turns (newest first, up to max_turns)
    turns_to_scan = list(reversed(history[-max_turns:]))

    extraction_timeout = timeout if timeout is not None else settings.extraction_timeout_normal

    for i, turn in enumerate(turns_to_scan):
        try:
            message = turn.get("content", "")
            if not message:
                continue

            logger.debug(f"Scanning turn {i+1}/{len(turns_to_scan)}: {message[:50]}...")

            # Run extractor on this turn
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: extractor(
                        conversation_history=history[:len(history)-i],
                        user_message=message
                    )
                ),
                timeout=extraction_timeout
            )

            # Extract value from result
            if isinstance(result, dict):
                field_name = field_path.split(".")[-1]
                value = result.get(field_name) or result.get("value")
                confidence = result.get("confidence", 0.5)
            else:
                field_name = field_path.split(".")[-1]
                value = getattr(result, field_name, None) or getattr(result, "value", None)
                confidence = getattr(result, "confidence", 0.5)

            # If we found a value, use it!
            if value is not None:
                set_nested_field(state, field_path, value)
                logger.info(
                    f"✅ Retroactively found {field_path} = {value} "
                    f"(turn -{i+1}, confidence: {confidence})"
                )

                # Store scan metadata
                metadata_path = f"{field_path}_scan_metadata"
                set_nested_field(state, metadata_path, {
                    "extraction_method": "retroactive_scan",
                    "turns_back": i + 1,
                    "confidence": confidence
                })

                return state

        except asyncio.TimeoutError:
            logger.debug(f"Timeout scanning turn {i+1}")
            continue
        except Exception as e:
            logger.debug(f"Error scanning turn {i+1}: {e}")
            continue

    # Scanned all turns, found nothing
    logger.info(f"⚠️ Retroactive scan found no {field_path} in {len(turns_to_scan)} turns")

    if "errors" not in state:
        state["errors"] = []
    state["errors"].append(f"scan_failed_{field_path}")

    return state
