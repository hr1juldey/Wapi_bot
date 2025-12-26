#!/usr/bin/env python3
"""Disposable demo to test Frappe Yawlit client (read-only operations).

This is a simple script to verify the Frappe client works correctly.
Tests only read-only operations (service catalog, vehicle types, categories).

Usage:
    python test_frappe_client_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clients.frappe_yawlit import YawlitClient


async def main():
    """Run read-only tests on Frappe Yawlit client."""

    print("=" * 70)
    print("Frappe Yawlit Client - Read-Only Demo")
    print("=" * 70)
    print()

    # Initialize client (reads from ../.env.txt)
    print("📡 Initializing Yawlit client...")
    client = YawlitClient()
    print(f"✅ Connected to: {client.config.base_url}")
    print()

    try:
        # Test 1: Get Vehicle Types
        print("🚗 Test 1: Fetching vehicle types...")
        try:
            result = await client.service_catalog.get_vehicle_types()
            # Parse nested response: {'message': {'success': True, 'vehicle_types': [...]}}
            message = result.get('message', {})
            vehicle_types = message.get('vehicle_types', [])
            print(f"✅ Found {len(vehicle_types)} vehicle types:")
            for vtype in vehicle_types:
                print(f"   - {vtype.get('vehicle_type', 'Unknown')}")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()

        # Test 2: Get Service Categories
        print("📦 Test 2: Fetching service categories...")
        try:
            result = await client.service_catalog.get_categories()
            # Parse response: {'message': [...]}
            categories = result.get('message', [])
            print(f"✅ Found {len(categories)} service categories:")
            for cat in categories:
                print(f"   - {cat.get('category_name', 'Unknown')} ({cat.get('category_slug', 'N/A')})")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()

        # Test 3: Get Filtered Services (all services)
        print("🔧 Test 3: Fetching all services...")
        try:
            result = await client.service_catalog.get_filtered_services()
            # Parse response: {'message': {'success': True, 'services': [...]}}
            message = result.get('message', {})
            services = message.get('services', [])
            print(f"✅ Found {len(services)} services:")
            for service in services[:5]:  # Show first 5
                name = service.get('product_name', 'Unknown')
                price = service.get('base_price', 'N/A')
                vehicle_type = service.get('vehicle_type', 'N/A')
                print(f"   - {name} (₹{price}, {vehicle_type})")
            if len(services) > 5:
                print(f"   ... and {len(services) - 5} more")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()

        # Test 4: Get Filtered Services (by vehicle type)
        print("🚗 Test 4: Fetching Hatchback services...")
        try:
            result = await client.service_catalog.get_filtered_services(
                vehicle_type="Hatchback"
            )
            message = result.get('message', {})
            services = message.get('services', [])
            print(f"✅ Found {len(services)} Hatchback services:")
            for service in services[:3]:  # Show first 3
                name = service.get('product_name', 'Unknown')
                price = service.get('base_price', 'N/A')
                freq_type = service.get('frequency_type', 'N/A')
                print(f"   - {name} (₹{price}, {freq_type})")
            if len(services) > 3:
                print(f"   ... and {len(services) - 3} more")
        except Exception as e:
            print(f"❌ Failed: {e}")
        print()

        print("=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)

    except Exception as e:
        print("=" * 70)
        print(f"❌ Demo failed with error: {e}")
        print("=" * 70)
        raise

    finally:
        # Clean up
        await client.close()
        print("\n🔒 Client connection closed")


if __name__ == "__main__":
    asyncio.run(main())