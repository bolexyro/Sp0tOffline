import string
import random
import base64


def generate_random_string(length=32):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))


def encode_to_base64(input_string):
    # Convert the string to bytes
    byte_data = input_string.encode('utf-8')

    # Encode the bytes to Base64
    base64_bytes = base64.b64encode(byte_data)

    # Convert bytes back to string
    return base64_bytes.decode('utf-8')
