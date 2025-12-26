"""Addon catalog message builder.

Displays available addons with prices and descriptions.
Allows multiple addon selection using numbered options.
"""

from workflows.shared.state import BookingState


class AddonCatalogBuilder:
    """Build addon selection message.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build addon catalog message from state.

        Args:
            state: Current booking state with available_addons

        Returns:
            Formatted addon catalog message
        """
        addons = state.get("available_addons", [])

        if not addons:
            return "No additional services available at this time."

        message = "✨ *Optional Add-Ons*\n\n"
        message += "Enhance your service with these optional extras:\n\n"

        # List addons with numbering
        for idx, addon in enumerate(addons, 1):
            addon_name = addon.get("addon_name", "Unknown")
            price = addon.get("price", 0)
            description = addon.get("description", "")

            message += f"{idx}. *{addon_name}* - ₹{price}\n"
            if description:
                message += f"   {description}\n"
            message += "\n"

        # Instructions
        message += "Reply with:\n"
        message += "• *Numbers* (e.g., 1, 2, 3) to add services\n"
        message += "• *SKIP* to continue without add-ons\n"

        return message
