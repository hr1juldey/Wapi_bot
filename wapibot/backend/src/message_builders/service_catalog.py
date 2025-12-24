"""Service catalog message builder.

SOLID Principles:
- Single Responsibility: ONLY builds service catalog messages
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from typing import List, Dict, Any
from workflows.shared.state import BookingState


class ServiceCatalogBuilder:
    """Build service catalog messages from filtered services.

    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        # After filtering services by vehicle type
        await send_message.node(state, ServiceCatalogBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build service catalog message from state.

        Args:
            state: Current booking state with filtered_services

        Returns:
            Formatted service catalog message

        Example:
            state = {
                "filtered_services": [
                    {"product_name": "Premium Wash", "base_price": 499, "description": "..."},
                    {"product_name": "Basic Wash", "base_price": 299, "description": "..."}
                ],
                ...
            }
            builder = ServiceCatalogBuilder()
            message = builder(state)
        """
        # Get filtered services
        services = state.get("filtered_services", [])

        if not services:
            return "Sorry, no services are available for your vehicle type at the moment."

        # Build catalog header
        message = "Here are the available services for your vehicle:\n\n"

        # Format each service
        for idx, service in enumerate(services, 1):
            product_name = service.get("product_name", "Service")
            base_price = service.get("base_price", 0)
            description = service.get("description", "")

            # Service entry
            message += f"{idx}. *{product_name}* - ₹{base_price}\n"

            # Add description if available (truncate if too long)
            if description:
                desc_short = description[:80] + "..." if len(description) > 80 else description
                message += f"   {desc_short}\n"

            message += "\n"

        # Add selection prompt
        message += "Please reply with the service number you'd like to book, "
        message += "or ask me for more details about any service."

        return message
