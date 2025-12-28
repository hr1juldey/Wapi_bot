"""Address selection message builder.

Extracted from address_group.py - shows saved addresses for user selection.

Implements MessageBuilder Protocol for use with send_message.node().
"""

from workflows.shared.state import BookingState


class AddressSelectionBuilder:
    """Build address selection message.

    Shows customer's saved addresses with numbered options.
    """

    def __call__(self, state: BookingState) -> str:
        """Build address selection message from state.

        Args:
            state: Current booking state with addresses and customer

        Returns:
            Formatted address selection message
        """
        addresses = state.get("addresses", [])
        customer_name = state.get("customer", {}).get("first_name", "there")

        # Build address list
        address_list = []
        for idx, addr in enumerate(addresses, 1):
            line1 = addr.get("address_line1", "")
            line2 = addr.get("address_line2", "")
            city = addr.get("city", "")
            pincode = addr.get("pincode", "")

            # Format address nicely
            full_addr = line1
            if line2:
                full_addr += f", {line2}"
            full_addr += f"\n   {city} - {pincode}"

            address_list.append(f"{idx}. {full_addr}")

        addresses_text = "\n\n".join(address_list)

        return f"""Hi {customer_name}! 👋

Where would you like us to service your vehicle?

Your saved addresses:

{addresses_text}

Please reply with the number of your preferred location (e.g., "1" or "2")."""