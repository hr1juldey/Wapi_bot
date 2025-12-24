"""Atomic nodes for V2 architecture.

These are fundamental, reusable nodes that work with ANY configuration.
They replace 100+ domain-specific nodes with 8 atomic nodes + 2 utility modules.

Inspired by Blender's geometry nodes design principles:
- Single responsibility
- Explicit dependencies (no hidden state)
- Dataflow programming (state in → state out)
- Composability through configuration

## Workflow Nodes (8 atomic nodes)

These are the core nodes used in LangGraph workflows:

1. extract.node - Extract ANY data with ANY DSPy module
2. validate.node - Validate ANY data with ANY Pydantic model
3. confidence_gate.node - Gate workflow based on ANY confidence function
4. scan.node - Retroactively scan history for ANY missing data
5. merge.node - Merge ANY data with confidence-based strategy
6. call_api.node - Call ANY HTTP API with request builders
7. send_message.node - Send WhatsApp messages with ANY message builder
8. transform.node - Transform ANY data with ANY transformer function

## Utility Modules (for configuration/introspection)

These help discover available configurations:

7. read_signature - List/import available DSPy signatures
8. read_model - List/import available Pydantic models

Example:
    # Extract name
    extract.node(state, NameExtractor(), "customer.first_name")

    # Extract phone (SAME node, different config!)
    extract.node(state, PhoneExtractor(), "customer.phone")

    # Validate name
    validate.node(state, Name, "customer", ["first_name"])

    # Call Yawlit API
    call_api.node(state, yawlit_request_builder, "customer_data")

    # Same node, different configurations!
"""

from nodes.atomic.extract import node as extract_node
from nodes.atomic.validate import node as validate_node
from nodes.atomic.confidence_gate import node as confidence_gate_node, get_gate_decision
from nodes.atomic.scan import node as scan_node
from nodes.atomic.merge import node as merge_node
from nodes.atomic.call_api import node as call_api_node
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node

# Utility modules for introspection
from nodes.atomic import read_signature
from nodes.atomic import read_model

__all__ = [
    # Workflow nodes
    "extract_node",
    "validate_node",
    "confidence_gate_node",
    "get_gate_decision",
    "scan_node",
    "merge_node",
    "call_api_node",
    "send_message_node",
    "transform_node",

    # Utility modules
    "read_signature",
    "read_model",
]
