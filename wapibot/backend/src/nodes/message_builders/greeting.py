"""Greeting message builder for existing customers.

SOLID Principles:
- Single Responsibility: ONLY builds greeting messages
- Open/Closed: Extensible via subclassing if needed
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from typing import Optional
from workflows.shared.state import BookingState


class GreetingBuilder:
    """Build personalized greeting messages for returning customers.

    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        await send_message.node(state, GreetingBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build greeting message from state.

        Args:
            state: Current booking state with customer data

        Returns:
            Personalized greeting message

        Example:
            state = {
                "customer": {"first_name": "Rahul", "last_name": "Sharma"},
                ...
            }
            builder = GreetingBuilder()
            message = builder(state)
            # "Hi Rahul! Welcome back to Yawlit! 👋"
        """
        # Get customer data
        customer = state.get("customer", {})
        first_name = customer.get("first_name", "")

        # Build personalized greeting
        if first_name:
            greeting = f"Hi {first_name}! Welcome back to Yawlit! 👋"
        else:
            greeting = "Hello! Welcome back to Yawlit! 👋"

        # Add helpful context
        message = f"{greeting}\n\n"
        message += "I'm here to help you book your car service. "
        message += "What would you like to do today?"

        return message
