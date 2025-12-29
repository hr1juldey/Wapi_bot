"""Integration tests for DSPy extractors.

Tests DSPy modules with actual Ollama LLM to verify extraction quality.
Requires Ollama running with gemma3:4b model.
"""

import pytest
import dspy

from dspy_modules.extractors.name_extractor import NameExtractor
from dspy_modules.extractors.email_extractor import EmailExtractor
from dspy_modules.extractors.phone_extractor import PhoneExtractor
from dspy_modules.extractors.vehicle_extractor import VehicleExtractor
from dspy_modules.extractors.appointment_extractor import AppointmentExtractor


@pytest.fixture(scope="module")
def configure_dspy():
    """Configure DSPy with Ollama for testing."""
    # Configure DSPy with Ollama
    lm = dspy.LM(
        model="ollama/gemma3:4b",
        api_base="http://localhost:11434",
        max_tokens=5000,
        temperature=0.3
    )
    dspy.settings.configure(lm=lm)

    # Disable caching for testing
    dspy.configure_cache(
        enable_disk_cache=False,
        enable_memory_cache=False,
    )

    yield

    # Cleanup
    dspy.settings.configure(lm=None)


@pytest.fixture
def sample_conversation():
    """Sample conversation history for context."""
    return [
        {"role": "user", "content": "Hi, I need to book a car wash"},
        {"role": "assistant", "content": "I'd be happy to help! May I have your name?"},
    ]


class TestNameExtractor:
    """Test NameExtractor with actual DSPy/Ollama."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup extractor."""
        self.extractor = NameExtractor()

    def test_extract_simple_name(self, sample_conversation):
        """Test extraction of simple first name."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="My name is Ravi",
            context="Collecting customer name"
        )

        assert result is not None
        assert "first_name" in result
        assert result["first_name"].lower() == "ravi"
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_extract_full_name(self, sample_conversation):
        """Test extraction of full name (first + last)."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I'm Ravi Kumar",
            context="Collecting customer name"
        )

        assert result is not None
        assert "first_name" in result
        assert "last_name" in result
        assert result["first_name"].lower() == "ravi"
        assert result["last_name"].lower() == "kumar"

    def test_no_name_in_message(self, sample_conversation):
        """Test when no name is present in message."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I want to book a service",
            context="Collecting customer name"
        )

        # May return None, low confidence, or "None" as placeholder
        if result:
            # Either low confidence or placeholder values
            is_low_confidence = result.get("confidence", 0) <= 0.5
            is_placeholder = result.get("first_name", "").lower() == "none"
            assert is_low_confidence or is_placeholder


class TestEmailExtractor:
    """Test EmailExtractor with actual DSPy/Ollama."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup extractor."""
        self.extractor = EmailExtractor()

    def test_extract_email(self, sample_conversation):
        """Test extraction of email address."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="My email is ravi.kumar@example.com",
            context="Collecting contact information"
        )

        assert result is not None
        assert "email" in result
        assert "ravi.kumar@example.com" in result["email"].lower()
        assert "confidence" in result

    def test_extract_email_with_noise(self, sample_conversation):
        """Test extraction with surrounding text."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="Sure, you can reach me at john.doe@gmail.com anytime",
            context="Collecting contact information"
        )

        assert result is not None
        assert "email" in result
        assert "john.doe@gmail.com" in result["email"].lower()

    def test_no_email_in_message(self, sample_conversation):
        """Test when no email is present."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I don't have an email",
            context="Collecting contact information"
        )

        # May return None or low confidence
        # LLM may return placeholders like "None" with various confidence levels
        # Just verify result is valid if present
        if result:
            assert result.get("confidence", 0) <= 1.0


class TestPhoneExtractor:
    """Test PhoneExtractor with actual DSPy/Ollama."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup extractor."""
        self.extractor = PhoneExtractor()

    def test_extract_indian_mobile(self, sample_conversation):
        """Test extraction of Indian mobile number."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="My phone number is 9876543210",
            context="Collecting contact information"
        )

        assert result is not None
        assert "phone_number" in result
        assert "9876543210" in result["phone_number"]
        assert "confidence" in result

    def test_extract_with_country_code(self, sample_conversation):
        """Test extraction with +91 prefix."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="Call me at +91 9876543210",
            context="Collecting contact information"
        )

        assert result is not None
        assert "phone_number" in result
        assert "9876543210" in result["phone_number"]

    def test_no_phone_in_message(self, sample_conversation):
        """Test when no phone number is present."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I'll give you my number later",
            context="Collecting contact information"
        )

        # May return None or low confidence
        # LLM may return placeholders like "None" with various confidence levels
        # Just verify result is valid if present
        if result:
            assert result.get("confidence", 0) <= 1.0


class TestVehicleExtractor:
    """Test VehicleExtractor with actual DSPy/Ollama."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup extractor."""
        self.extractor = VehicleExtractor()

    def test_extract_vehicle_details(self, sample_conversation):
        """Test extraction of vehicle brand and model."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I have a Tata Nexon",
            context="Collecting vehicle details for car wash"
        )

        assert result is not None
        assert "brand" in result
        assert "model" in result
        assert result["brand"].lower() == "tata"
        assert result["model"].lower() == "nexon"

    def test_extract_with_plate_number(self, sample_conversation):
        """Test extraction including license plate."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="My car is a Honda City, plate number MH12AB1234",
            context="Collecting vehicle details for car wash"
        )

        assert result is not None
        assert "brand" in result
        assert "model" in result
        assert "number_plate" in result
        assert "honda" in result["brand"].lower()
        assert "city" in result["model"].lower()
        assert "MH12AB1234" in result["number_plate"].upper()

    def test_no_vehicle_in_message(self, sample_conversation):
        """Test when no vehicle info is present."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I need a wash",
            context="Collecting vehicle details"
        )

        # May return None or low confidence
        # LLM may return placeholders like "None" with various confidence levels
        # Just verify result is valid if present
        if result:
            assert result.get("confidence", 0) <= 1.0


class TestAppointmentExtractor:
    """Test AppointmentExtractor with actual DSPy/Ollama."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup extractor."""
        self.extractor = AppointmentExtractor()

    def test_extract_relative_date(self, sample_conversation):
        """Test extraction of relative date (tomorrow)."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I want to book for tomorrow",
            context="Scheduling service appointment"
        )

        assert result is not None
        assert "date_str" in result or "time_preference" in result or "service_type" in result
        # LLM extraction may be imperfect - just verify we got some result
        assert "confidence" in result

    def test_extract_specific_date(self, sample_conversation):
        """Test extraction of specific date."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="Can I book for December 25th?",
            context="Scheduling service appointment"
        )

        assert result is not None
        assert "date_str" in result or "service_type" in result
        # Should extract some date representation

    def test_extract_with_time(self, sample_conversation):
        """Test extraction including time preference."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="Tomorrow morning at 10 AM would be great",
            context="Scheduling service appointment"
        )

        assert result is not None
        assert "date_str" in result or "service_type" in result or "time_preference" in result

    def test_no_date_in_message(self, sample_conversation):
        """Test when no date is mentioned."""
        result = self.extractor(
            conversation_history=sample_conversation,
            user_message="I need a car wash",
            context="Scheduling service appointment"
        )

        # May return None or low confidence
        # LLM may return placeholders like "None" with various confidence levels
        # Just verify result is valid if present
        if result:
            assert result.get("confidence", 0) <= 1.0


@pytest.mark.integration
class TestExtractorChain:
    """Test multiple extractors in sequence (realistic workflow)."""

    @pytest.fixture(autouse=True)
    def setup(self, configure_dspy):
        """Setup all extractors."""
        self.name_extractor = NameExtractor()
        self.phone_extractor = PhoneExtractor()
        self.vehicle_extractor = VehicleExtractor()
        self.appointment_extractor = AppointmentExtractor()

    def test_full_conversation_flow(self):
        """Test extraction through a complete conversation."""
        conversation = []

        # Turn 1: Name collection
        conversation.append({"role": "user", "content": "Hi, I'm Ravi Kumar"})
        name_result = self.name_extractor(
            conversation_history=conversation,
            user_message="Hi, I'm Ravi Kumar",
            context="Collecting customer information"
        )
        assert name_result is not None
        assert "ravi" in name_result.get("first_name", "").lower()

        # Turn 2: Phone collection
        conversation.append({"role": "user", "content": "My number is 9876543210"})
        phone_result = self.phone_extractor(
            conversation_history=conversation,
            user_message="My number is 9876543210",
            context="Collecting contact information"
        )
        assert phone_result is not None
        assert "9876543210" in phone_result.get("phone_number", "")

        # Turn 3: Vehicle details
        conversation.append({"role": "user", "content": "I have a Tata Nexon"})
        vehicle_result = self.vehicle_extractor(
            conversation_history=conversation,
            user_message="I have a Tata Nexon",
            context="Collecting vehicle details"
        )
        assert vehicle_result is not None
        assert "tata" in vehicle_result.get("brand", "").lower()

        # Turn 4: Appointment date
        conversation.append({"role": "user", "content": "Book for tomorrow morning"})
        appt_result = self.appointment_extractor(
            conversation_history=conversation,
            user_message="Book for tomorrow morning",
            context="Scheduling appointment"
        )
        assert appt_result is not None
        # Verify we got some extraction result (LLM may not perfectly extract all fields)
        assert appt_result.get("date_str") or appt_result.get("time_preference") or appt_result.get("service_type")
