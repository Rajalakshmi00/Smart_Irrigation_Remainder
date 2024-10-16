import os
secret_key = os.urandom(24)  # Generates a random 24-byte string
print(secret_key.hex())  # Converts to a hex representation
