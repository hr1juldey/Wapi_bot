"""Bargaining response message builder with 4-stage escalation.

Stages:
1. Distract - Highlight value proposition
2. Nudge - Emphasize quality and benefits
3. Coupon - Offer discount (requires API call)
4. Escalate - Transfer to human support
"""

from workflows.shared.state import BookingState


class BargainingResponseBuilder:
    """Build bargaining responses based on escalation stage.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build bargaining response based on stage.

        Args:
            state: Current booking state with bargaining_stage

        Returns:
            Appropriate response for current bargaining stage
        """
        stage = state.get("bargaining_stage", 1)
        service_name = state.get("selected_service", {}).get("product_name", "this service")

        if stage == 1:
            return self._distract_response(service_name, state)
        elif stage == 2:
            return self._nudge_response(service_name, state)
        elif stage == 3:
            return self._coupon_response(state)
        else:
            return self._escalate_response()

    def _distract_response(self, service_name: str, state: BookingState) -> str:
        """Stage 1: Distract with value proposition."""
        price = state.get("total_price", 0)
        return (
            f"💎 I understand pricing is important!\n\n"
            f"For ₹{price}, *{service_name}* includes:\n"
            f"✅ Professional service\n"
            f"✅ Quality guarantee\n"
            f"✅ Convenient home service\n\n"
            f"This is our best value for the quality you receive!"
        )

    def _nudge_response(self, service_name: str, state: BookingState) -> str:
        """Stage 2: Nudge with benefits and quality."""
        return (
            f"🌟 We want to give you the best experience!\n\n"
            f"*{service_name}* is priced competitively for:\n"
            f"• Expert technicians\n"
            f"• Premium products\n"
            f"• Satisfaction guaranteed\n\n"
            f"Can I help you proceed with booking?"
        )

    def _coupon_response(self, state: BookingState) -> str:
        """Stage 3: Offer coupon/discount."""
        coupon_code = state.get("offered_coupon", "FIRST10")
        discount = state.get("coupon_discount", "10%")

        return (
            f"🎁 Special offer just for you!\n\n"
            f"Use code *{coupon_code}* for {discount} off!\n\n"
            f"This is the best discount I can offer.\n"
            f"Ready to book?"
        )

    def _escalate_response(self) -> str:
        """Stage 4: Escalate to human support."""
        return (
            "💬 I want to make sure you get the best deal!\n\n"
            "Let me connect you with my team who can discuss "
            "custom pricing for your needs.\n\n"
            "Transferring you now..."
        )
