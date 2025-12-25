#!/usr/bin/env python3
"""WAPI WhatsApp Client Demo - Test message sending and webhook reception.

This script demonstrates WAPI integration for sending WhatsApp messages.
To receive replies, you MUST set up ngrok webhook forwarding first.

Prerequisites:
    1. ngrok installed and authenticated
    2. Backend server running on port 8000
    3. WAPI webhook configured in dashboard

Setup Steps:
    1. Start backend server:
       cd backend && uvicorn src.main:app --reload --port 8000

    2. Start ngrok tunnel:
       ngrok http 8000

    3. Copy ngrok HTTPS URL (e.g., https://abc123.ngrok.io)

    4. Configure webhook in WAPI dashboard:
       - Go to https://wapi.in.net/dashboard
       - Navigate to Webhooks settings
       - Set Webhook URL: https://abc123.ngrok.io/api/v1/wapi/webhook
       - Save configuration

    5. Run this script:
       python test_wapi_demo.py

    6. Send a reply from your WhatsApp
       - Backend will receive webhook and log it

Usage:
    python test_wapi_demo.py
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clients.wapi.wapi_client import WAPIClient
from core.config import settings


async def main():
    """Run WAPI message sending demo."""

    print("=" * 70)
    print("WAPI WhatsApp Client Demo")
    print("=" * 70)
    print()

    # IMPORTANT: Change this to your WhatsApp test number
    # Format: Country code + number (e.g., 919876543210 for India)
    TEST_PHONE_NUMBER = "916290818033"  # Target phone number

    print("⚠️  PREREQUISITES CHECK:")
    print("=" * 70)
    print("1. Backend server running on port 8000?")
    print("   Command: uvicorn src.main:app --reload --port 8000")
    print()
    print("2. ngrok tunnel active on port 8000?")
    print("   Command: ngrok http 8000")
    print()
    print("3. WAPI webhook configured?")
    print("   Dashboard: https://wapi.in.net/dashboard")
    print("   Webhook URL format: https://YOUR-NGROK-URL.ngrok.io/api/v1/wapi/webhook")
    if settings.wapi_webhook_url:
        print(f"   Current webhook URL: {settings.wapi_webhook_url}")
    print()
    print("4. Test phone number updated in script?")
    print(f"   Current: {TEST_PHONE_NUMBER}")
    print("=" * 70)
    print()

    response = input("Have you completed all prerequisites? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\n❌ Please complete prerequisites first. Exiting...")
        return

    print()
    print("=" * 70)

    # Initialize WAPI client (reads from ../.env.txt)
    print("📡 Initializing WAPI client...")
    client = WAPIClient()
    print(f"✅ Connected to: {client.base_url}")
    print(f"📱 Using phone number ID: {client.from_phone_number_id}")
    print()

    try:
        # Test 1: Send a simple text message
        print("💬 Test 1: Sending test message to WhatsApp...")
        print(f"   Recipient: {TEST_PHONE_NUMBER}")
        print()

        message_text = (
            "🤖 *WAPI Test Message*\n\n"
            "Hello! This is a test message from WapiBot backend.\n\n"
            "If you receive this message, the WAPI integration is working correctly!\n\n"
            "✅ *Next Steps:*\n"
            "1. Reply to this message with any text\n"
            "2. Check backend logs for webhook reception\n"
            "3. Your reply should be logged by the webhook endpoint\n\n"
            "_This is an automated test message._"
        )

        try:
            result = await client.send_message(
                phone_number=TEST_PHONE_NUMBER,
                message_body=message_text
            )

            print("✅ Message sent successfully!")
            print()
            print("📊 Response from WAPI:")
            print("-" * 70)

            # Pretty print the response
            if isinstance(result, dict):
                for key, value in result.items():
                    print(f"   {key}: {value}")
            else:
                print(f"   {result}")

            print("-" * 70)
            print()

        except Exception as e:
            print(f"❌ Failed to send message: {e}")
            print()
            print("Common issues:")
            print("  - Check WAPI_BEARER_TOKEN in .env.txt")
            print("  - Verify phone number format (country code + number)")
            print("  - Check WAPI account balance/credits")
            print("  - Verify phone number ID is correct")
            raise

        # Instructions for receiving replies
        print("=" * 70)
        print("📥 RECEIVING REPLIES")
        print("=" * 70)
        print()
        print("To test webhook reception:")
        print()
        print("1. Send a reply from WhatsApp to the message you just received")
        print()
        print("2. Check backend server logs for webhook activity:")
        print("   Look for: POST /api/v1/wapi/webhook")
        print()
        print("3. Backend should log the webhook payload:")
        print("   - Sender phone number")
        print("   - Message content")
        print("   - Message timestamp")
        print()
        print("4. If webhook is NOT received:")
        print("   a) Verify ngrok tunnel is active: ngrok http 8000")
        print("   b) Check ngrok web interface: http://localhost:4040")
        print("   c) Verify webhook URL in WAPI dashboard matches ngrok URL")
        print("   d) Check WAPI webhook logs in dashboard")
        print()
        print("=" * 70)
        print()

        # Test 2: Get contact information
        print("📋 Test 2: Fetching contact information...")
        try:
            contact = await client.get_contact(TEST_PHONE_NUMBER)

            if contact:
                print("✅ Contact found:")
                print("-" * 70)
                if isinstance(contact, dict):
                    for key, value in contact.items():
                        print(f"   {key}: {value}")
                else:
                    print(f"   {contact}")
                print("-" * 70)
            else:
                print("ℹ️  Contact not found in WAPI")
                print("   (This is normal if contact hasn't messaged before)")
        except Exception as e:
            print(f"⚠️  Contact lookup failed: {e}")
            print("   (This is non-critical - main test is message sending)")
        print()

        print("=" * 70)
        print("✅ Demo completed successfully!")
        print("=" * 70)
        print()
        print("🎯 Summary:")
        print("  ✅ WAPI client initialized")
        print("  ✅ Test message sent to WhatsApp")
        print("  ℹ️  Reply to the message to test webhook reception")
        print()
        print("📚 Next Steps:")
        print("  1. Check WhatsApp - you should have received the test message")
        print("  2. Reply to test webhook integration")
        print("  3. Monitor backend logs for webhook POST requests")
        print("  4. Review webhook payload in logs")
        print()

    except Exception as e:
        print("=" * 70)
        print(f"❌ Demo failed with error: {e}")
        print("=" * 70)
        print()
        print("🔍 Troubleshooting:")
        print("  1. Check .env.txt has valid WAPI credentials")
        print("  2. Verify WAPI account is active with credits")
        print("  3. Confirm phone number format is correct")
        print("  4. Check network connectivity")
        print()
        raise

    finally:
        # Clean up
        await client.close()
        print("🔒 Client connection closed")


if __name__ == "__main__":
    asyncio.run(main())
