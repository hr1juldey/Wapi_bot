"""Filter services transformer.

SOLID Principles:
- Single Responsibility: ONLY filters services by vehicle type
- Open/Closed: Extensible via subclassing
- Dependency Inversion: Implements Transformer Protocol
"""

from typing import List, Dict, Any
from workflows.shared.state import BookingState


class FilterServicesByVehicle:
    """Filter services based on vehicle type.

    Implements Transformer Protocol for use with transform.node().

    Usage:
        # Filter all_services to get only those matching vehicle type
        await transform.node(
            state,
            FilterServicesByVehicle(),
            "all_services",
            "filtered_services"
        )
    """

    def __call__(self, services: List[Dict[str, Any]], state: BookingState) -> List[Dict[str, Any]]:
        """Filter services by vehicle type from state.

        Args:
            services: List of all available services
            state: Current booking state with vehicle information

        Returns:
            Filtered list of services matching vehicle type

        Example:
            services = [
                {"product_name": "Car Wash", "vehicle_type": "Hatchback", "base_price": 299},
                {"product_name": "SUV Wash", "vehicle_type": "SUV", "base_price": 499},
                {"product_name": "Basic Wash", "vehicle_type": "Hatchback", "base_price": 199}
            ]
            state = {"vehicle": {"vehicle_type": "Hatchback"}}

            result = transformer(services, state)
            # Returns 2 Hatchback services
        """
        # Get vehicle type from state
        vehicle = state.get("vehicle", {})
        vehicle_type = vehicle.get("vehicle_type", "")

        if not vehicle_type:
            # No vehicle type specified, return all services
            return services

        # Filter services by vehicle type
        filtered = [
            service for service in services
            if service.get("vehicle_type", "").lower() == vehicle_type.lower()
        ]

        return filtered
