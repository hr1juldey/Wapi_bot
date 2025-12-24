# Pydantic v2 Built-in Types - Improvement Recommendations

## Summary of Manual Implementations That Have Pydantic v2 Equivalents

### 1. Phone Number Validation ⚠️ **HIGH PRIORITY**

**Current Implementation** (`models/customer.py:100-124`):
- Custom `@field_validator` with manual regex for Indian phone numbers
- Manual cleaning and normalization

**Pydantic v2 Alternative**:
```python
from pydantic_extra_types.phone_numbers import PhoneNumber

# Option 1: Generic phone number (requires pydantic-extra-types + phonenumbers)
phone_number: PhoneNumber

# Option 2: Regional phone number
from typing import Annotated
phone_number: Annotated[PhoneNumber, Field(default_region='IN')]
```

**Installation Required**:
```bash
pip install pydantic-extra-types phonenumbers
```

**Benefits**:
- Leverages Google's libphonenumber library
- Automatic formatting and validation
- International phone number support
- E.164 format standardization

**Files to Update**:
- `models/customer.py` (Phone class)
- `utils/validation_utils.py` (is_valid_indian_phone, normalize_phone functions)

---

### 2. Email Validation ✅ **READY TO USE**

**Current Implementation**:
- Custom regex in `utils/validation_utils.py:74-86` (is_valid_email)
- Custom regex in `fallbacks/email_fallback.py:14`

**Pydantic v2 Built-in** (already available):
```python
from pydantic import EmailStr

class Contact(BaseModel):
    email: EmailStr  # Automatic validation, no custom regex needed
```

**Benefits**:
- RFC 5322 compliant validation
- Built into core Pydantic (no extra package)
- Normalized lowercase email strings
- Industry-standard validation

**Files to Update**:
- Create `models/customer.py` Email model (if needed)
- Update `utils/validation_utils.py` to use EmailStr validator
- Update `fallbacks/email_fallback.py` to use EmailStr pattern

---

### 3. Date/DateTime Validation 📅 **RECOMMENDED**

**Current Implementation** (`models/appointment.py:15-75`):
- Custom Date model with date_str and parsed_date fields
- Manual parsing and validation

**Pydantic v2 Built-ins**:
```python
from pydantic import FutureDate, PastDate, AwareDatetime, NaiveDatetime
from datetime import date, datetime

class Appointment(BaseModel):
    # Appointment dates should be in the future
    appointment_date: FutureDate

    # Or use standard datetime with automatic parsing
    scheduled_time: AwareDatetime  # Timezone-aware
```

**Benefits**:
- Automatic parsing from ISO format, timestamps, strings
- Type safety with specific date/datetime variants
- Built-in past/future validation
- Timezone awareness enforcement

**Files to Update**:
- `models/appointment.py` (Date, Appointment classes)

---

### 4. String Pattern Validation 🔤 **OPTIONAL (Style Preference)**

**Current Implementation** (`models/customer.py:21`):
```python
first_name: str = Field(
    ...,
    pattern=r'^[A-Za-z][A-Za-z\'-]*([ .][A-Za-z][A-Za-z\'-]*)*$'
)
```

**Pydantic v2 Modern Approach**:
```python
from typing import Annotated
from pydantic import StringConstraints

FirstName = Annotated[
    str,
    StringConstraints(
        pattern=r'^[A-Za-z][A-Za-z\'-]*([ .][A-Za-z][A-Za-z\'-]*)*$',
        min_length=1,
        max_length=50,
        strip_whitespace=True
    )
]

class Name(BaseModel):
    first_name: FirstName
```

**Benefits**:
- Type reusability
- Better static analysis support
- Modern Pydantic v2 style (constr deprecated in v3)

**Files to Consider**:
- `models/customer.py` (Name class)
- `models/vehicle.py` (brand, model fields)

---

### 5. Numeric Constraints ✅ **ALREADY OPTIMAL**

**Current Implementation**:
```python
confidence: float = Field(ge=0.0, le=1.0)
```

**Status**: ✅ This is already the correct Pydantic v2 approach!

Pydantic provides `PositiveFloat`, `NegativeFloat`, etc., but for 0-1 ranges, using `Field(ge=0, le=1)` is the recommended approach.

---

## Implementation Priority

### Phase 1: High Impact ⚡
1. **Email**: Use `EmailStr` (no dependencies, immediate benefit)
2. **Phone**: Use `PhoneNumber` from pydantic-extra-types (requires install)

### Phase 2: Enhancement 📈
3. **Date/DateTime**: Use `FutureDate`, `AwareDatetime` for better type safety
4. **String Patterns**: Migrate to `Annotated` + `StringConstraints` (v3 preparation)

---

## Required Packages

```bash
# For phone number validation
pip install pydantic-extra-types phonenumbers

# Core pydantic (already installed)
# pydantic>=2.0
```

---

## References

- [Pydantic v2 Types Documentation](https://docs.pydantic.dev/latest/concepts/types/)
- [Pydantic v2 API Types](https://docs.pydantic.dev/latest/api/types/)
- [Phone Numbers - Pydantic Validation](https://docs.pydantic.dev/latest/api/pydantic_extra_types_phone_numbers/)
- [Validators - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [Fields - Pydantic Validation](https://docs.pydantic.dev/latest/concepts/fields/)

---

## Migration Strategy

1. Start with EmailStr (no dependencies)
2. Install pydantic-extra-types for PhoneNumber
3. Update models one at a time
4. Run tests after each update
5. Update fallbacks and utilities to match new types
