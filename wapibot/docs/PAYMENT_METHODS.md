# 💳 Yawlit Payment Methods

## Active Payment Modes

### 1️⃣ UPI (Primary Digital Payment)
- **UPI ID**: `7980866011@upi`
- **Status**: ✅ Active
- **Used in**: QR code generation for instant digital payments
- **Processing**: Instant settlement via NPCI

### 2️⃣ Bank Transfer
- **Bank**: State Bank of India
- **Branch**: Kalikapur
- **IFSC Code**: [REDACTED]
- **Account Number**: [REDACTED]
- **Account Name**: Yawlit Automotives Private Limited
- **Status**: Available for direct transfers
- **Processing**: 1-2 business days

### 3️⃣ Cheque Payment
- **Payee Name**: YAWLIT AUTOMOTIVES PVT. LTD.
- **Status**: Available as alternative payment mode
- **Processing**: 3-5 business days for clearance

## UPI QR Configuration

The system generates UPI QR codes with the following format:
```
upi://pay?pa=7980866011@upi&am={AMOUNT}&cu=INR&tn={DESCRIPTION}
```

**Example Generated QR**:
- Amount: ₹500
- Description: "Yawlit Booking {BOOKING_ID}"
- QR Image Location: `/data/qr_codes/{SESSION_ID}.png`

## Payment Reminders

Customers receive reminders at:
- **0 hours** (Instant): When QR code is generated
- **24 hours**: First reminder
- **48 hours**: Second reminder
- **72 hours**: Final reminder
- **Cutoff**: 7 days (payment marked as expired after this)

All reminders include:
- Generated UPI QR code image
- Payment amount
- Booking reference
- Contact support link

## Payment Reconciliation

### Admin Confirmation
Endpoint: `POST /admin/payments/confirm`

```json
{
  "session_id": "uuid",
  "admin_user": "admin@yawlit.com",
  "payment_proof": "reference-number (optional)",
  "notes": "Payment confirmation notes (optional)"
}
```

**Actions**:
1. Marks payment session as CONFIRMED
2. Cancels all pending reminders
3. Triggers workflow to complete booking
4. Logs transaction for audit trail

### Payment Status Tracking
Endpoint: `GET /admin/payments/status/{session_id}`

Returns:
- Current payment status (PENDING, CONFIRMED, EXPIRED, CANCELLED)
- Amount and booking reference
- Confirmation timestamp and admin user
- Reminder count and schedule

## Security Notes

⚠️ **BANKING INFORMATION REDACTED**: Sensitive banking details (account numbers, IFSC codes) are stored securely and not logged in system messages or audit trails.

✅ **UPI Information**: Only the UPI ID is required for QR generation and is safe to display to customers.

## Environment Configuration

```bash
# In .env.txt
UPI_ID=7980866011@upi
PAYMENT_INSTANT_REMINDER=true
PAYMENT_REMINDER_INTERVALS=[24,48,72]
PAYMENT_CUTOFF_HOURS=168
```

---

**Last Updated**: 2025-12-26
**Team**: Yawlit
