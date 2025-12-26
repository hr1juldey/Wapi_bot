"""Vehicle options message builder.

SOLID Principles:
- Single Responsibility: ONLY builds vehicle selection messages
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements MessageBuilder Protocol
"""

from workflows.shared.state import BookingState


class VehicleOptionsBuilder:
    """Build vehicle selection messages from available vehicles.

    Implements MessageBuilder Protocol for use with send_message.node().

    Usage:
        # After fetching vehicles with multiple options
        await send_message.node(state, VehicleOptionsBuilder())
    """

    def __call__(self, state: BookingState) -> str:
        """Build vehicle selection message from state.

        Args:
            state: Current booking state with vehicle_options

        Returns:
            Formatted vehicle selection message
        """
        vehicles = state.get("vehicle_options", [])

        if not vehicles:
            return (
                "You don't have any vehicles registered. "
                "Please add a vehicle at https://yawlit.duckdns.org/customer/profile to continue."
            )

        # Build selection header
        message = "Which vehicle would you like to book for?\n\n"

        # Format each vehicle option
        for idx, vehicle in enumerate(vehicles, 1):
            make = vehicle.get("vehicle_make", "")
            model = vehicle.get("vehicle_model", "")
            number = vehicle.get("vehicle_number", "")
            v_type = vehicle.get("vehicle_type", "")

            # Vehicle entry
            message += f"{idx}. *{make} {model}* ({number})"
            if v_type:
                message += f" - {v_type}"
            message += "\n"

        # Add selection prompt
        message += "\nReply with the number (1, 2, 3, etc.)"

        return message
