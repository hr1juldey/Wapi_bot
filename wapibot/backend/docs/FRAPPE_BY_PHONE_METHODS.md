# Frappe `_by_phone` Methods Audit

## Overview

This document catalogs all `_by_phone` methods in the Frappe Yawlit client and provides recommendations for WhatsApp bot usage.

**What are `_by_phone` methods?**
- Phone-based API methods that don't require session authentication
- Designed for WhatsApp bot integration where sessions are impractical
- Accept `phone_number` parameter instead of relying on authenticated session

---

## Existing `_by_phone` Methods

### 1. `get_profile_by_phone()` ✅ CURRENTLY USED

**Location**: `src/clients/frappe_yawlit/customer/profile_client.py:48`

**Purpose**: Fetch complete customer profile using phone number

**Parameters**:
```python
async def get_profile_by_phone(self, phone_number: str) -> Dict[str, Any]
```

**Returns**:
```python
{
    "exists": True,
    "customer": {...},  # customer_uuid, first_name, last_name, etc.
    "vehicles": [...],  # All customer vehicles
    "addresses": [...], # All customer addresses
    "bookings": [...],  # Recent bookings
}
```

**Usage**:
- Used in `workflows/node_groups/profile_group.py`
- First step in existing user booking workflow
- Fetches all profile data in one API call

**Status**: ✅ **Already integrated and working**

---

### 2. `create_booking_by_phone()` ✅ MIGRATED TO

**Location**: `src/clients/frappe_yawlit/booking/create_client.py:67`

**Purpose**: Create booking without session authentication

**Parameters**:
```python
async def create_booking_by_phone(
    self,
    phone_number: str,  # 10 digits, no country code
    booking_data: Dict[str, Any]  # See below
) -> Dict[str, Any]
```

**booking_data structure**:
```python
{
    "product_id": "SERV-001",
    "booking_date": "2025-12-25",
    "slot_id": "SLOT-001",
    "vehicle_id": "VEH-001",
    "address_id": "ADDR-001",
    "electricity_provided": 1,  # 1=yes, 0=no
    "water_provided": 1,        # 1=yes, 0=no
    "addon_ids": ["ADDON-001", "ADDON-002"],
    "payment_mode": "Pay Now"
}
```

**Returns**:
```python
{
    "success": True,
    "booking_id": "BKG-2025-001",  # Direct field (not nested)
    "total_amount": 1500.0,
    "message": "Booking created successfully"
}
```

**Usage**:
- **Migrated to** in `workflows/node_groups/booking_group.py:120`
- Replaces session-based `create_booking()` method
- Handles phone normalization (removes "91" country code)

**Status**: ✅ **Just migrated to (Phase 3)**

---

### 3. `_check_by_phone()` ⚠️ PRIVATE HELPER

**Location**: `src/clients/frappe_yawlit/customer/lookup_client.py:89`

**Purpose**: Internal helper to check if customer exists by phone

**Parameters**:
```python
async def _check_by_phone(self, phone: str) -> Dict[str, Any]
```

**Usage**:
- Private method (leading underscore)
- Used internally by `check_customer_exists()` method
- Not intended for direct use in workflows

**Status**: ⚠️ **Internal use only - not for workflows**

---

## Methods WITHOUT `_by_phone` Variants

### Customer Address Management

**File**: `src/clients/frappe_yawlit/customer/address_client.py`

**Methods**:
- `get_addresses()` - Get all customer addresses
- `add_address(address_data)` - Add new address
- `update_address(address_name, address_data)` - Update address
- `delete_address(address_name)` - Delete address

**Recommendation**: ❌ **No `_by_phone` version needed**

**Rationale**:
- Addresses already included in `get_profile_by_phone()` response
- Address modifications require customer_uuid which we get from profile
- Session-based methods work fine after authentication

---

### Booking Management

**File**: `src/clients/frappe_yawlit/booking/manage_client.py`

**Methods**:
- `get_bookings(filters)` - Get customer bookings
- `get_booking_details(booking_id)` - Get specific booking details
- `reschedule_booking(booking_id, new_slot)` - Reschedule booking
- `cancel_booking(booking_id, reason)` - Cancel booking
- `check_cancellation_eligibility(booking_id)` - Check if can cancel

**Recommendation**: ⚠️ **Consider for future if reschedule/cancel features needed**

**Rationale**:
- Current booking flow only needs creation (already has `_by_phone`)
- Booking history available in `get_profile_by_phone()` response
- Reschedule/cancel features not yet implemented in WhatsApp bot
- If/when implemented, `_by_phone` versions would be useful

**Future API Suggestions** (if backend team adds them):
```python
# Useful for WhatsApp bot reschedule/cancel flows
async def reschedule_booking_by_phone(phone: str, booking_id: str, new_slot: Dict) -> Dict
async def cancel_booking_by_phone(phone: str, booking_id: str, reason: str) -> Dict
async def get_booking_history_by_phone(phone: str, limit: int = 10) -> Dict
```

---

## Summary & Recommendations

### ✅ Current State is Sufficient

The existing `_by_phone` methods cover the core booking workflow:

1. **Profile Fetching**: `get_profile_by_phone()` ✅
   - Gets customer, vehicles, addresses, booking history in one call

2. **Booking Creation**: `create_booking_by_phone()` ✅
   - Creates bookings without session
   - Returns real booking_id from backend

### 🔮 Future Enhancements (Out of Current Scope)

If/when the WhatsApp bot needs to support:
- **Booking rescheduling** → Request `reschedule_booking_by_phone()` from backend team
- **Booking cancellation** → Request `cancel_booking_by_phone()` from backend team
- **Address management** → Continue using session-based methods (sufficient)

### 📋 Migration Complete

All necessary `_by_phone` methods are now integrated:
- ✅ Profile fetching (already was using `_by_phone`)
- ✅ Booking creation (just migrated to `_by_phone`)
- ✅ Phone normalization handling implemented
- ✅ Backward-compatible response extraction

**No further `_by_phone` migrations needed for current scope.**

---

## Technical Notes

### Phone Number Format

All `_by_phone` methods expect:
- **10 digits** (no country code)
- Example: `"9876543210"`

WhatsApp sends:
- **12 digits** (with country code)
- Example: `"919876543210"`

**Solution**: Phone normalization in `booking_group.py:130-140`
```python
phone = conversation_id
if phone.startswith("91") and len(phone) == 12:
    phone = phone[2:]  # Remove country code
```

### API Response Differences

**Old `create_booking()` response** (session-based):
```python
{
    "message": {
        "booking_id": "BKG-2025-001",
        "total_amount": 1500.0
    }
}
```

**New `create_booking_by_phone()` response**:
```python
{
    "success": True,
    "booking_id": "BKG-2025-001",  # ← Direct field
    "total_amount": 1500.0,
    "message": "Booking created successfully"
}
```

**Solution**: Backward-compatible extraction pattern
```python
booking_id = (
    booking_response.get("booking_id") or
    booking_response.get("message", {}).get("booking_id", "Unknown")
)
```

---

**Document Version**: 1.0
**Last Updated**: 2025-12-27
**Author**: Claude Code (Automated Migration)
