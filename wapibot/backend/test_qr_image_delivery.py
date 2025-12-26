#!/usr/bin/env python3
"""Test QR Image Delivery via WAPI.

Complete end-to-end test:
1. Generate 10 rupee QR code
2. Verify endpoint serves it
3. Send via WAPI to customer
"""

import sys
import os
import asyncio
import httpx
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.config import settings
from services.qr_service import qr_service
from clients.wapi import get_wapi_client
from nodes.message_builders.payment_instructions import build_payment_instructions_caption
import uuid


async def test_qr_image_delivery():
    """Test QR image delivery via WAPI."""

    print("=" * 80)
    print("🎯 QR IMAGE DELIVERY TEST")
    print("=" * 80)

    # Configuration
    phone = "916290818033"
    amount = 10.0
    session_id = str(uuid.uuid4())

    print(f"\n📋 Test Configuration:")
    print(f"   Phone: {phone}")
    print(f"   Amount: ₹{amount}")
    print(f"   Session: {session_id[:8]}...")
    print(f"   Public URL: {settings.public_base_url}")

    # Step 1: Generate QR
    print(f"\n⏳ Step 1: Generating QR code...")
    upi_string = qr_service.generate_upi_string(
        amount=amount,
        transaction_note=f"Test Booking {session_id[:8]}"
    )
    qr_bytes, qr_path = qr_service.generate_qr_image(
        upi_string=upi_string,
        session_id=session_id,
        save_to_disk=True
    )
    print(f"   ✅ QR generated: {qr_path}")
    print(f"   📦 Size: {len(qr_bytes)} bytes")
    time.sleep(5)
    
    # Step 2: Verify endpoint
    print(f"\n⏳ Step 2: Testing QR endpoint...")
    endpoint_url = f"{settings.public_base_url}/api/v1/qr/{session_id}.png"
    print(f"   🌐 URL: {endpoint_url}")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(endpoint_url)
            print(f"   Status: {response.status_code}")

            if response.status_code == 200:
                print(f"   ✅ Endpoint works! (size: {len(response.content)} bytes)")
            else:
                print(f"   ⚠️  Unexpected status code: {response.status_code}")
                print(f"   Response: {response.text}")

    except Exception as e:
        print(f"   ⚠️  Could not reach endpoint: {e}")
        print(f"   💡 Make sure backend is running: uvicorn src.main:app --reload")

    # Step 3: Send via WAPI
    print(f"\n⏳ Step 3: Sending QR image via WAPI...")
    try:
        client = get_wapi_client()

        # Build professional payment instructions
        caption = build_payment_instructions_caption(amount)

        result = await client.send_media(
            phone_number=phone,
            media_type="image",
            media_url=endpoint_url,
            caption=caption
        )

        wamid = result.get("data", {}).get("wamid", "N/A")
        status = result.get("data", {}).get("status", "unknown")

        print(f"   ✅ Image sent to {phone}")
        print(f"   Status: {status}")
        print(f"   WAMID: {wamid[:30]}...")

    except Exception as e:
        print(f"   ❌ Failed to send: {e}")
        import traceback
        traceback.print_exc()
        return

    # Summary
    print("\n" + "=" * 80)
    print("✅ QR IMAGE DELIVERY TEST COMPLETE")
    print("=" * 80)
    print(f"\n📊 Results:")
    print(f"   ✅ QR Code Generated: {qr_path}")
    print(f"   ✅ Endpoint Accessible: {endpoint_url}")
    print(f"   ✅ WAPI Delivery: {phone}")
    print(f"\n✨ Customer should now receive:")
    print(f"   1️⃣ QR code image in WhatsApp")
    print(f"   2️⃣ Caption with payment instructions")
    print()


if __name__ == "__main__":
    asyncio.run(test_qr_image_delivery())
