"""State machine service for conversation flow.

Determines next conversation state based on completeness and intent.
"""

from typing import Dict, Any
from models.booking_state import BookingState
from services.completeness_service import completeness_service


class StateMachineService:
    """Manage conversation state transitions."""

    # Conversation states
    STATE_GREETING = "greeting"
    STATE_COLLECTING_INFO = "collecting_info"
    STATE_CONFIRMING = "confirming"
    STATE_CREATING_BOOKING = "creating_booking"
    STATE_COMPLETED = "completed"
    STATE_CANCELLED = "cancelled"

    def determine_next_state(
        self,
        current_state: str,
        intent: str,
        completeness: float,
        is_complete: bool
    ) -> str:
        """Determine next conversation state.

        Args:
            current_state: Current state
            intent: Classified user intent
            completeness: Completeness score (0-1)
            is_complete: Whether all required fields filled

        Returns:
            Next state
        """
        # Handle cancellation intent
        if intent == "booking_cancel":
            return self.STATE_CANCELLED

        # Handle greeting
        if current_state == self.STATE_GREETING:
            if intent in ["booking_new", "booking_inquiry"]:
                return self.STATE_COLLECTING_INFO
            return self.STATE_GREETING

        # Handle info collection
        if current_state == self.STATE_COLLECTING_INFO:
            if is_complete:
                return self.STATE_CONFIRMING
            return self.STATE_COLLECTING_INFO

        # Handle confirmation
        if current_state == self.STATE_CONFIRMING:
            if intent == "confirmation":
                return self.STATE_CREATING_BOOKING
            elif intent == "correction":
                return self.STATE_COLLECTING_INFO
            return self.STATE_CONFIRMING

        # Handle booking creation
        if current_state == self.STATE_CREATING_BOOKING:
            return self.STATE_COMPLETED

        return current_state

    def should_confirm(
        self,
        state: BookingState,
        current_state: str,
        completeness: float
    ) -> bool:
        """Check if should ask for confirmation.

        Args:
            state: Current booking state
            current_state: Current conversation state
            completeness: Completeness score

        Returns:
            True if should ask for confirmation
        """
        # Only confirm when all required fields filled
        is_complete = completeness_service.is_complete(state)

        if not is_complete:
            return False

        # Confirm when entering confirming state
        if current_state == self.STATE_CONFIRMING:
            return True

        return False


# Singleton instance
state_machine_service = StateMachineService()
