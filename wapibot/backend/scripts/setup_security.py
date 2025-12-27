"""Security setup script.

One-time setup: generates keys, encrypts secrets in .env.txt
"""

import os
import secrets
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from security.secret_manager import SecretManager


def generate_master_key(key_path: Path) -> bytes:
    """Generate AES-256 master key.

    Args:
        key_path: Path to save master key

    Returns:
        32-byte AES key
    """
    key = secrets.token_bytes(32)  # 256 bits
    key_path.write_bytes(key)
    return key


def generate_api_key(prefix: str = "sk") -> str:
    """Generate secure API key.

    Args:
        prefix: Key prefix (e.g., "sk", "live", "test")

    Returns:
        Secure random API key
    """
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


def update_env_file(env_path: Path, updates: dict):
    """Update .env.txt file with new values.

    Args:
        env_path: Path to .env.txt
        updates: Dict of key-value pairs to update
    """
    lines = env_path.read_text().splitlines()
    updated_lines = []

    for line in lines:
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            updated_lines.append(line)
            continue

        # Check if line contains a key to update
        if "=" in line:
            key = line.split("=")[0].strip()
            if key in updates:
                updated_lines.append(f"{key}={updates[key]}")
                continue

        updated_lines.append(line)

    # Add new keys if they don't exist
    existing_keys = {line.split("=")[0].strip() for line in lines if "=" in line}
    for key, value in updates.items():
        if key not in existing_keys:
            updated_lines.append(f"{key}={value}")

    env_path.write_text("\n".join(updated_lines) + "\n")


def main():
    """Run security setup."""
    print("\n🔐 WapiBot Security Setup")
    print("=" * 50)

    # Paths
    backend_dir = Path(__file__).parent.parent
    master_key_path = backend_dir / "master.key"
    env_path = backend_dir / ".env.txt"

    # Backup .env.txt
    if env_path.exists():
        backup_path = env_path.with_suffix(".txt.backup")
        backup_path.write_text(env_path.read_text())
        print(f"✓ Backup saved: {backup_path.name}")

    # Generate master key
    if not master_key_path.exists():
        generate_master_key(master_key_path)
        print(f"✓ Generated master.key (AES-256 key)")
    else:
        print(f"⚠️  master.key already exists, skipping")

    # Initialize secret manager
    secret_manager = SecretManager(str(master_key_path))

    # Generate JWT secret
    jwt_secret = secrets.token_urlsafe(32)
    jwt_secret_enc = secret_manager.encrypt_value(jwt_secret)
    print(f"✓ Generated JWT secret key")

    # Generate API keys
    admin_key = generate_api_key("sk_live")
    brain_key = generate_api_key("sk_brain")
    print(f"✓ Generated Admin API key: {admin_key[:20]}...")
    print(f"✓ Generated Brain API key: {brain_key[:20]}...")

    # Encrypt API keys
    admin_key_enc = secret_manager.encrypt_value(admin_key)
    brain_key_enc = secret_manager.encrypt_value(brain_key)

    # Generate field encryption key
    field_key = secrets.token_urlsafe(32)
    field_key_enc = secret_manager.encrypt_value(field_key)
    print(f"✓ Generated field encryption key")

    # Update .env.txt
    updates = {
        "JWT_SECRET_KEY": jwt_secret_enc,
        "API_KEY_ADMIN": admin_key_enc,
        "API_KEY_BRAIN": brain_key_enc,
        "FIELD_ENCRYPTION_KEY": field_key_enc,
        "SECRETS_ENCRYPTED": "True",
        "MASTER_KEY_PATH": "./master.key",
    }

    update_env_file(env_path, updates)
    print(f"✓ Updated .env.txt with encrypted secrets")

    # Instructions
    print("\n" + "=" * 50)
    print("⚠️  IMPORTANT NEXT STEPS:")
    print("=" * 50)
    print("1. Add to .gitignore: master.key")
    print("2. Store master.key securely (DO NOT commit)")
    print("3. Save these API keys securely:")
    print(f"   - Admin Key: {admin_key}")
    print(f"   - Brain Key: {brain_key}")
    print("4. Set ENVIRONMENT=production in .env.txt for production")
    print("5. Restart server: uvicorn src.main:app --reload")
    print("\n✅ Security setup complete!")


if __name__ == "__main__":
    main()
