"""Message builders for send_message atomic node.

Message builders implement the MessageBuilder Protocol and generate
message text from BookingState.

They are used with send_message.node():
    await send_message.node(state, GreetingBuilder())
    await send_message.node(state, ServiceCatalogBuilder())
"""

from nodes.message_builders.greeting import GreetingBuilder
from nodes.message_builders.service_catalog import ServiceCatalogBuilder
from nodes.message_builders.booking_confirmation import BookingConfirmationBuilder
from nodes.message_builders.vehicle_options import VehicleOptionsBuilder
from nodes.message_builders.date_preference_prompt import DatePreferencePromptBuilder
from nodes.message_builders.time_preference_menu import TimePreferenceMenuBuilder
from nodes.message_builders.date_preference_menu import DatePreferenceMenuBuilder
from nodes.message_builders.grouped_slots import GroupedSlotsBuilder

__all__ = [
    "GreetingBuilder",
    "ServiceCatalogBuilder",
    "BookingConfirmationBuilder",
    "VehicleOptionsBuilder",
    "DatePreferencePromptBuilder",
    "TimePreferenceMenuBuilder",
    "DatePreferenceMenuBuilder",
    "GroupedSlotsBuilder",
]
