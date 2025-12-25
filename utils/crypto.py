"""
Credential encryption/decryption utilities using Fernet symmetric encryption.
"""

import os
import json
from cryptography.fernet import Fernet
from typing import Tuple


class CredentialManager:
    """Manages encrypted storage of login credentials."""

    def __init__(self, credentials_file: str = "config/credentials.enc",
                 key_file: str = "config/.key"):
        self.credentials_file = credentials_file
        self.key_file = key_file
        self.cipher = None

    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create a new one."""
        if os.path.exists(self.key_file):
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            # Create new key
            key = Fernet.generate_key()
            # Ensure config directory exists
            os.makedirs(os.path.dirname(self.key_file), exist_ok=True)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            # Secure the key file
            os.chmod(self.key_file, 0o600)
            return key

    def _get_cipher(self) -> Fernet:
        """Get or create Fernet cipher instance."""
        if self.cipher is None:
            key = self._get_or_create_key()
            self.cipher = Fernet(key)
        return self.cipher

    def encrypt_credentials(self, username: str, password: str, domain: str) -> None:
        """
        Encrypt and save credentials to file.

        Args:
            username: NTU network username
            password: NTU password
            domain: NTU domain (e.g., 'Student')
        """
        cipher = self._get_cipher()

        # Create credentials dictionary
        creds = {
            'username': username,
            'password': password,
            'domain': domain
        }

        # Convert to JSON and encrypt
        creds_json = json.dumps(creds).encode('utf-8')
        encrypted = cipher.encrypt(creds_json)

        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.credentials_file), exist_ok=True)

        # Save encrypted credentials
        with open(self.credentials_file, 'wb') as f:
            f.write(encrypted)

        # Secure the credentials file
        os.chmod(self.credentials_file, 0o600)

        print(f"✓ Credentials encrypted and saved to {self.credentials_file}")

    def decrypt_credentials(self) -> Tuple[str, str, str]:
        """
        Decrypt and return stored credentials.

        Returns:
            Tuple of (username, password, domain)

        Raises:
            FileNotFoundError: If credentials file doesn't exist
            ValueError: If decryption fails
        """
        if not os.path.exists(self.credentials_file):
            raise FileNotFoundError(
                f"Credentials file not found: {self.credentials_file}\n"
                "Please run setup first to store credentials."
            )

        cipher = self._get_cipher()

        try:
            # Read and decrypt
            with open(self.credentials_file, 'rb') as f:
                encrypted = f.read()

            decrypted = cipher.decrypt(encrypted)
            creds = json.loads(decrypted.decode('utf-8'))

            return (creds['username'], creds['password'], creds['domain'])

        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {e}")

    def credentials_exist(self) -> bool:
        """Check if credentials file exists."""
        return os.path.exists(self.credentials_file)

    def delete_credentials(self) -> None:
        """Delete stored credentials and encryption key."""
        if os.path.exists(self.credentials_file):
            os.remove(self.credentials_file)
            print(f"✓ Deleted {self.credentials_file}")

        if os.path.exists(self.key_file):
            os.remove(self.key_file)
            print(f"✓ Deleted {self.key_file}")


def setup_credentials() -> None:
    """Interactive setup to store encrypted credentials."""
    print("\n" + "="*60)
    print("NTU SSO CREDENTIAL SETUP")
    print("="*60)
    print("\nYour credentials will be encrypted and stored securely.")
    print("The encryption key is stored separately and not shared.\n")

    username = input("Enter NTU Network Username (e.g., AJITESH001): ").strip()
    password = input("Enter NTU Password: ").strip()
    domain = input("Enter Domain (e.g., Student): ").strip()

    if not all([username, password, domain]):
        print("\n❌ Error: All fields are required!")
        return

    manager = CredentialManager()
    manager.encrypt_credentials(username, password, domain)

    print("\n✓ Setup complete! Your credentials are now stored securely.")
    print("  They will be used automatically when running the scraper.\n")


if __name__ == "__main__":
    # Allow running this file directly to setup credentials
    setup_credentials()
