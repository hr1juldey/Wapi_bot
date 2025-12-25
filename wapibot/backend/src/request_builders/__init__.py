"""Request builders for call_api atomic node.

Request builders implement the RequestBuilder Protocol and generate
HTTP request configurations from BookingState.

They are used with call_api.node():
    await call_api.node(state, FrappeCustomerLookup(), "customer_data")
    await call_api.node(state, FrappeServicesRequest(), "services")
"""

from request_builders.frappe_customer_lookup import FrappeCustomerLookup
from request_builders.frappe_services import FrappeServicesRequest
from request_builders.frappe_create_booking import FrappeCreateBookingRequest

__all__ = [
    "FrappeCustomerLookup",
    "FrappeServicesRequest",
    "FrappeCreateBookingRequest",
]
