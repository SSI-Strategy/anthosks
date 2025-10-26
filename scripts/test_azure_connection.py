#!/usr/bin/env python3
"""Test Azure OpenAI connection using DefaultAzureCredential."""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from azure.identity import DefaultAzureCredential, AzureCliCredential
    from openai import AzureOpenAI
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing required package: {e}")
    print("\nInstall required packages:")
    print("  pip install azure-identity openai python-dotenv")
    sys.exit(1)

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def test_connection():
    """Test Azure OpenAI authentication and basic call."""

    print("🔐 Testing Azure OpenAI Connection")
    print("=" * 60)

    # Check environment variables
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")

    print(f"Endpoint:   {endpoint}")
    print(f"Deployment: {deployment}")
    print(f"API Version: {api_version}")
    print(f"API Key:    {'[Set]' if api_key else '[Not Set - will try Azure CLI]'}")
    print("-" * 60)

    if not all([endpoint, deployment, api_version]):
        print("❌ Missing required environment variables in .env file")
        print("   Required: AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, AZURE_OPENAI_API_VERSION")
        return False

    # Try API key first, then fall back to Azure CLI
    if api_key:
        print("\n1️⃣  Using API Key Authentication...")
        print("   ✅ API key found in environment")

        # Initialize OpenAI client with API key
        print("\n2️⃣  Initializing Azure OpenAI Client...")
        try:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=api_key,
                api_version=api_version
            )
            print("   ✅ Azure OpenAI client initialized")
        except Exception as e:
            print(f"   ❌ Client initialization failed: {e}")
            return False
    else:
        # Try Azure CLI credential (requires custom subdomain)
        print("\n1️⃣  Testing Azure CLI Authentication...")
        print("   ⚠️  No API key found, trying Azure CLI credentials...")
        try:
            credential = AzureCliCredential()
            token = credential.get_token("https://cognitiveservices.azure.com/.default")
            print("   ✅ Azure CLI authentication successful")
            print(f"   Token expires: {token.expires_on}")
        except Exception as e:
            print(f"   ❌ Azure CLI auth failed: {e}")
            print("\n   Run: az login")
            print("   Or add AZURE_OPENAI_API_KEY to .env file")
            return False

        # Initialize OpenAI client with token
        print("\n2️⃣  Initializing Azure OpenAI Client...")
        try:
            client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_version=api_version,
                azure_ad_token_provider=lambda: credential.get_token(
                    "https://cognitiveservices.azure.com/.default"
                ).token
            )
            print("   ✅ Azure OpenAI client initialized")
        except Exception as e:
            print(f"   ❌ Client initialization failed: {e}")
            print("\n   Note: Token auth requires custom subdomain endpoint.")
            print("   Add AZURE_OPENAI_API_KEY to .env file instead.")
            return False

    # Test simple completion
    print("\n3️⃣  Testing Model Completion...")
    try:
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Respond with exactly: 'Connection test successful'"}
            ],
            max_tokens=50,
            temperature=0
        )

        result = response.choices[0].message.content
        tokens_used = response.usage.total_tokens

        print(f"   ✅ Test completion successful")
        print(f"   Response: {result}")
        print(f"   Tokens used: {tokens_used} (prompt: {response.usage.prompt_tokens}, completion: {response.usage.completion_tokens})")

        return True

    except Exception as e:
        print(f"   ❌ Completion failed: {e}")
        print(f"\n   Error details: {type(e).__name__}")
        if hasattr(e, 'status_code'):
            print(f"   Status code: {e.status_code}")
        return False

def main():
    """Main entry point."""
    print("\n" + "=" * 60)
    print("AZURE OPENAI CONNECTION TEST")
    print("=" * 60 + "\n")

    success = test_connection()

    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nYou can now use Azure OpenAI in your application!")
        print("The connection is authenticated via Azure CLI credentials.")
    else:
        print("❌ TESTS FAILED")
        print("=" * 60)
        print("\nPlease fix the issues above and try again.")
    print()

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
