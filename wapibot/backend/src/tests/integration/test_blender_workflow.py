"""Test script for Blender-style booking workflow."""

import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_workflow():
    """Test the Blender-style workflow with phone 6290818033."""

    # Initialize checkpointer
    from core.checkpointer import checkpointer_manager

    print("🔧 Initializing checkpointer...")
    db_path = Path("checkpoints.db")
    await checkpointer_manager.initialize(db_path)
    print("✅ Checkpointer initialized\n")

    # Import and create workflow
    from workflows.booking_workflow_v2 import create_booking_workflow

    print("📦 Creating Blender-style workflow...")
    workflow = create_booking_workflow()
    print("✅ Workflow created\n")

    # Test state
    initial_state = {
        "conversation_id": "6290818033",  # Your phone number
        "user_message": "Hi",
        "history": []
    }

    print("=" * 60)
    print("🚀 TESTING BLENDER-STYLE WORKFLOW")
    print("=" * 60)
    print(f"📞 Phone: {initial_state['conversation_id']}")
    print(f"💬 Message: {initial_state['user_message']}")
    print("=" * 60)
    print()

    try:
        # Run workflow
        print("▶️  Running workflow...\n")

        config = {"configurable": {"thread_id": "6290818033"}}
        result = await workflow.ainvoke(initial_state, config)

        print("\n" + "=" * 60)
        print("✅ WORKFLOW COMPLETED SUCCESSFULLY")
        print("=" * 60)

        # Display results
        print("\n📊 RESULTS:")
        print("-" * 60)

        if result.get("customer"):
            customer = result["customer"]
            print(f"👤 Customer: {customer.get('first_name')} (UUID: {customer.get('customer_uuid')})")

        if result.get("vehicle"):
            vehicle = result["vehicle"]
            print(f"🚗 Vehicle: {vehicle.get('vehicle_make')} {vehicle.get('vehicle_model')} ({vehicle.get('vehicle_number')})")
        elif result.get("vehicle_options"):
            print(f"🚗 Vehicles: {len(result['vehicle_options'])} options available")

        if result.get("profile_complete"):
            print("✅ Profile: Complete")
        else:
            print("⚠️  Profile: Incomplete")

        if result.get("response"):
            print("\n💬 Response sent to user:")
            print(f"   {result['response']}")

        print("-" * 60)

    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ WORKFLOW FAILED")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        await checkpointer_manager.shutdown()
        print("✅ Done!")

if __name__ == "__main__":
    asyncio.run(test_workflow())
