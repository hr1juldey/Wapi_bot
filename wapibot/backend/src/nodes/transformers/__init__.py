"""Transformers for transform atomic node.

Transformers implement the Transformer Protocol and transform data
from source to target format.

They are used with transform.node():
    await transform.node(state, FilterServicesByVehicle(), "all_services", "filtered_services")
    await transform.node(state, FormatSlotOptions(), "slots", "formatted_slots")
"""

from nodes.transformers.filter_services import FilterServicesByVehicle
from nodes.transformers.format_slot_options import FormatSlotOptions
from nodes.transformers.filter_slots_by_preference import FilterSlotsByPreference
from nodes.transformers.group_slots_by_time import GroupSlotsByTime

__all__ = [
    "FilterServicesByVehicle",
    "FormatSlotOptions",
    "FilterSlotsByPreference",
    "GroupSlotsByTime",
]
