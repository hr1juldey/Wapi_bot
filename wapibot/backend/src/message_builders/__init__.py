"""Message builders for send_message atomic node.

Message builders implement the MessageBuilder Protocol and generate
message text from BookingState.

They are used with send_message.node():
    await send_message.node(state, GreetingBuilder())
    await send_message.node(state, ServiceCatalogBuilder())
"""

from message_builders.greeting import GreetingBuilder
from message_builders.service_catalog import ServiceCatalogBuilder
from message_builders.booking_confirmation import BookingConfirmationBuilder

__all__ = [
    "GreetingBuilder",
    "ServiceCatalogBuilder",
    "BookingConfirmationBuilder",
]
