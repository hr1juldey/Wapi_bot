"""Addon selection message builder (personalized version).

Extracted from addon_group.py - personalized with customer name and service.
Different from addon_catalog.py which is generic.

Implements MessageBuilder Protocol for use with send_message.node().
"""

from workflows.shared.state import BookingState


class AddonSelectionBuilder:
    """Build personalized addon selection message.

    Shows available addons with customer greeting and selected service context.
    """

    def __call__(self, state: BookingState) -> str:
        """Build addon selection message from state.

        Args:
            state: Current booking state with available_addons, selected_service, customer

        Returns:
            Formatted personalized addon message
        """
        addons = state.get("available_addons", [])
        service_name = state.get("selected_service", {}).get("product_name", "service")
        customer_name = state.get("customer", {}).get("first_name", "there")

        # Build addon list
        addon_list = []
        for idx, addon in enumerate(addons, 1):
            addon_name = addon.get("addon_name", "")
            price = addon.get("unit_price", 0)
            description = addon.get("description", "")

            addon_text = f"{idx}. *{addon_name}* - ₹{price}"
            if description:
                addon_text += f"\n   {description}"

            addon_list.append(addon_text)

        addons_text = "\n\n".join(addon_list)

        return f"""Great choice, {customer_name}! 🎉

Your selected service: *{service_name}*

Would you like to add any extras?

*Available Add-ons:*

{addons_text}

*To select:*
• Reply with numbers (e.g., "1 3" for addons 1 and 3)
• Reply "None" or "Skip" if you don't want any addons"""