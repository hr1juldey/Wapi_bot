"""V2 Full workflow demonstrating atomic node composition.

This workflow shows how atomic nodes compose to create complex behavior:
- Extract name with DSPy
- Validate extracted name
- Check confidence
- If low confidence, scan history retroactively
- Merge scanned data with confidence checking
- Generate response

Flow demonstrates:
- Multiple atomic nodes working together
- Conditional routing based on confidence
- Retroactive scanning (V1's strength)
- Confidence-based merging (fixes V1's bug)
"""

from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic import (
    extract_node,
    confidence_gate_node,
    get_gate_decision,
    scan_node,
    merge_node
)
from dspy_modules.extractors.name_extractor import NameExtractor
from fallbacks.name_fallback import RegexNameExtractor


# Configure extractors
name_extractor = NameExtractor()
regex_fallback = RegexNameExtractor()


# Node wrapper functions with specific configurations
async def extract_name(state: BookingState) -> BookingState:
    """Extract name using atomic extract node."""
    return await extract_node(
        state=state,
        extractor=name_extractor,
        field_path="customer.first_name",
        fallback_fn=lambda msg: regex_fallback.extract(msg),
        metadata_path="customer.extraction_metadata"
    )


async def check_name_confidence(state: BookingState) -> BookingState:
    """Check if extracted name has high confidence."""
    customer = state.get("customer", {})
    metadata = customer.get("extraction_metadata", {})
    confidence = metadata.get("confidence", 0.0)

    return await confidence_gate_node(
        state=state,
        confidence_path="customer.extraction_metadata.confidence",
        threshold=0.7,  # Require 70% confidence
        gate_name="name_confidence_check"
    )


async def scan_history_for_name(state: BookingState) -> BookingState:
    """Retroactively scan conversation history for name.

    This is V1's strength - if current extraction failed or has low confidence,
    scan previous turns to find the name.
    """
    return await scan_node(
        state=state,
        extractor=name_extractor,
        field_path="customer.first_name",
        max_turns=5,  # Scan last 5 turns
        skip_if_exists=False  # Always scan to find better data
    )


async def merge_scanned_name(state: BookingState) -> BookingState:
    """Merge scanned name with confidence checking.

    This prevents V1's bug where "Shukriya" overwrote "Sneha Reddy".
    Only merge if scanned data has higher confidence.
    """
    # Get scanned data
    scanned_metadata = state.get("customer", {}).get("first_name_scan_metadata", {})
    scanned_confidence = scanned_metadata.get("confidence", 0.0)

    if scanned_confidence > 0:
        # Scanned data found, merge it
        scanned_name = state.get("customer", {}).get("first_name", "")

        new_data = {
            "first_name": scanned_name,
            "extraction_method": "retroactive_scan"
        }

        return await merge_node(
            state=state,
            new_data=new_data,
            data_path="customer",
            new_confidence=scanned_confidence,
            confidence_field="confidence"
        )

    # No scanned data found, return unchanged
    return state


async def generate_response(state: BookingState) -> BookingState:
    """Generate response based on extracted name."""
    customer = state.get("customer", {})
    first_name = customer.get("first_name", "")
    extraction_method = customer.get("extraction_method", "unknown")
    confidence = customer.get("confidence", 0.0)

    if first_name and confidence >= 0.7:
        # High confidence name
        state["response"] = f"Nice to meet you, {first_name}! 👋"
        state["completeness"] = 0.3

        # Add debug info
        if extraction_method == "retroactive_scan":
            state["response"] += " (I found your name from our earlier conversation)"

    elif first_name and confidence >= 0.5:
        # Medium confidence - ask for confirmation
        state["response"] = f"Just to confirm, your name is {first_name}, right?"
        state["completeness"] = 0.2

    else:
        # Low confidence or no name - ask user
        state["response"] = "I didn't catch your name. What's your name?"
        state["completeness"] = 0.0

    return state


def create_v2_full_workflow() -> StateGraph:
    """Create V2 full workflow with atomic node composition.

    Flow:
        extract_name → check_confidence → [high/low]
                                            ↓ high
                                        generate_response → END
                                            ↓ low
                                        scan_history → merge_scanned → generate_response → END

    This demonstrates:
    - Atomic extract node with fallback
    - Confidence gating for conditional routing
    - Retroactive scanning (V1's strength)
    - Confidence-based merging (fixes V1's bug)
    - Response generation based on data quality
    """
    workflow = StateGraph(BookingState)

    # Add atomic nodes with configurations
    workflow.add_node("extract_name", extract_name)
    workflow.add_node("check_confidence", check_name_confidence)
    workflow.add_node("scan_history", scan_history_for_name)
    workflow.add_node("merge_scanned", merge_scanned_name)
    workflow.add_node("generate_response", generate_response)

    # Entry point
    workflow.set_entry_point("extract_name")

    # Always check confidence after extraction
    workflow.add_edge("extract_name", "check_confidence")

    # Conditional routing based on confidence
    workflow.add_conditional_edges(
        "check_confidence",
        get_gate_decision,
        {
            "high_confidence": "generate_response",  # Skip scanning
            "low_confidence": "scan_history"  # Try retroactive scan
        }
    )

    # After scanning, merge the data
    workflow.add_edge("scan_history", "merge_scanned")

    # After merging, generate response
    workflow.add_edge("merge_scanned", "generate_response")

    # End after response
    workflow.add_edge("generate_response", END)

    return workflow


# Compile workflow
v2_full_workflow = create_v2_full_workflow().compile()
