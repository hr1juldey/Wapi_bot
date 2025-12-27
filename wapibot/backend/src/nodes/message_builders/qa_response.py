"""Q&A response message builder.

Handles off-topic questions about services, pricing, policies, etc.
Provides helpful answers and redirects to booking flow.
"""

from workflows.shared.state import BookingState


class QAResponseBuilder:
    """Build Q&A response messages.

    Implements MessageBuilder Protocol for use with send_message.node().
    """

    def __call__(self, state: BookingState) -> str:
        """Build Q&A response from detected question type.

        Args:
            state: Current booking state with qa_question_type

        Returns:
            Helpful answer message
        """
        question_type = state.get("qa_question_type", "general")

        responses = {
            "hours": "🕒 We're open:\n"
                    "Monday-Saturday: 7AM - 8PM\n"
                    "Sunday: 8AM - 6PM\n\n"
                    "Would you like to book a service?",

            "location": "📍 We serve across the city!\n"
                       "Our mobile team comes to you.\n\n"
                       "Ready to book? Let's get started!",

            "services": "🚗 We offer:\n"
                       "• Car Wash\n"
                       "• Detailing\n"
                       "• Maintenance\n"
                       "• Repairs\n\n"
                       "Want to see specific prices? Let me help you book!",

            "general": "I'm here to help you book services! 🙂\n\n"
                      "I can answer basic questions, but booking is what I do best.\n\n"
                      "Shall we get started?"
        }

        return responses.get(question_type, responses["general"])
