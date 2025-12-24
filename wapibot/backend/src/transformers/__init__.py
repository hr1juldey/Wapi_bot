"""Transformers for transform atomic node.

Transformers implement the Transformer Protocol and transform data
from source to target format.

They are used with transform.node():
    await transform.node(state, FilterServicesByVehicle(), "all_services", "filtered_services")
    await transform.node(state, FormatSlotOptions(), "slots", "formatted_slots")
"""

from transformers.filter_services import FilterServicesByVehicle
from transformers.format_slot_options import FormatSlotOptions

__all__ = [
    "FilterServicesByVehicle",
    "FormatSlotOptions",
]
