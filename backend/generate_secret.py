import secrets
import base64

# Generate a secure random key
def generate_secret_key():
    # Generate 32 random bytes
    random_bytes = secrets.token_bytes(32)
    # Convert to base64 string
    secret_key = base64.b64encode(random_bytes).decode('utf-8')
    return secret_key

if __name__ == "__main__":
    secret = generate_secret_key()
    print("\nGenerated JWT Secret Key:")
    print("-" * 50)
    print(secret)
    print("-" * 50)
    print("\nAdd this to your .env file as:")
    print(f"JWT_SECRET={secret}") 