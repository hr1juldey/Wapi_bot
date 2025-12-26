"""Payment instructions message builder for QR code delivery.

Builds professional payment message with QR code and multiple payment modes.
"""

from core.config import settings


def build_payment_instructions_caption(amount: float) -> str:
    """Build professional payment instructions message with all payment modes.

    Args:
        amount: Payment amount in rupees

    Returns:
        Formatted message with payment instructions and payment modes
    """
    message = f"""Hey {settings.company_name} 🔥 fam,🙏🏻

{settings.payment_help_text} 📞

*Scan the QR code above to pay ₹{amount:.2f}*

Payment Modes:-

1️⃣ *UPI ID:* {settings.upi_id}

2️⃣ *Bank Transfer:*
   Bank: {settings.bank_name}
   Branch: {settings.bank_branch}
   IFSC: {settings.bank_ifsc}
   Account: {settings.bank_account_no}
   Name: {settings.bank_account_name}

3️⃣ *Cheque:* Issued in the name of "{settings.bank_account_name}"

Regards,
Team {settings.company_name}"""

    return message