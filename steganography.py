from PIL import Image
import os
import secrets
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PublicFormat, PrivateFormat, load_pem_private_key, load_pem_public_key, pkcs7

def encode_message(image_path, message, output_path, encrypted=False, password=None, preserve_quality=True):
    try:
        image = Image.open(image_path)
        image.verify()
        image = Image.open(image_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Image file not found at {image_path}")
    except Exception as e:
        raise Exception(f"Error: Unable to open or read image file. {e}")

    encoded_image = image.copy()
    binary_message = ''.join(format(ord(char), '08b') for char in message)

    if encrypted:  
        if not password:
            raise ValueError("Password is required for encryption.")

        salt = secrets.token_bytes(16) 
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode()) 

        iv = secrets.token_bytes(16) 
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        

        padder = padding.PKCS7(algorithms.AES.block_size).padder() 
        padded_binary_message = padder.update(binary_message.encode()) + padder.finalize()
        ciphertext = encryptor.update(padded_binary_message) + encryptor.finalize()
        
        binary_message_to_embed = salt + iv + ciphertext
        binary_message_to_embed_binary = ''.join(format(byte, '08b') for byte in binary_message_to_embed)

    else:
        binary_message_to_embed_binary = binary_message  

    binary_message_to_embed_binary += '1111111111111110'  

    pixels = list(encoded_image.getdata())
    if len(binary_message_to_embed_binary) > len(pixels) * 3:
        raise ValueError("Error: Message is too long to be encoded in this image.")

    new_pixels = []
    message_index = 0
    for pixel in pixels:
        new_pixel = list(pixel)
        for i in range(3):
            if message_index < len(binary_message_to_embed_binary):
                new_pixel[i] = (new_pixel[i] & ~1) | int(binary_message_to_embed_binary[message_index])
                message_index += 1
        new_pixels.append(tuple(new_pixel))

    encoded_image.putdata(new_pixels)
    try:
        encoded_image.save(output_path, "PNG")
    except Exception as e:
        raise Exception(f"Error: Unable to save encoaded image to {output_path}. {e}")
    return output_path

def decode_message(image_path, is_encrypted=False, password=None):
    try:
        image = Image.open(image_path)
        image.verify()
        image = Image.open(image_path)
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: Image file not found at {image_path}")
    except Exception as e:
        raise Exception(f"Error: Unable to open or read image file. {e}")

    pixels = list(image.getdata())
    binary_message_full = ''
    for pixel in pixels:
        for i in range(3):
            binary_message_full += str(pixel[i] & 1)

    end_marker = '1111111111111110'
    end_index = binary_message_full.find(end_marker)
    if end_index != -1:
        binary_message_bytes_str = binary_message_full[:end_index]
    else:
        binary_message_bytes_str = binary_message_full
        print(" Warning: No end marker found. Extracted data may be incorrect!")

    binary_message_bytes = [binary_message_bytes_str[i:i+8] for i in range(0, len(binary_message_bytes_str), 8) if len(binary_message_bytes_str[i:i+8]) == 8]
    binary_message_string = "".join(binary_message_bytes)

    if is_encrypted: 
        if not password:
            raise ValueError("Password is required for decryption of encrypted message.")
        if len(binary_message_string) < (16 + 16) * 8:  
            raise ValueError("Error: Invalid data format - Salt and IV are missing or too short.")

        salt_bytes_binary = binary_message_string[:16*8]  
        iv_bytes_binary = binary_message_string[16*8:32*8]  
        ciphertext_bytes_binary = binary_message_string[32*8:]  

        salt = bytes(int(salt_bytes_binary[i:i+8], 2) for i in range(0, len(salt_bytes_binary), 8)) 
        iv = bytes(int(iv_bytes_binary[i:i+8], 2) for i in range(0, len(iv_bytes_binary), 8))  
        ciphertext = bytes(int(ciphertext_bytes_binary[i:i+8], 2) for i in range(0, len(ciphertext_bytes_binary), 8))  

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
            backend=default_backend()
        )
        key = kdf.derive(password.encode())  

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted_padded_binary_message = decryptor.update(ciphertext) + decryptor.finalize()

        unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()  
        decrypted_binary_message_bytes = unpadder.update(decrypted_padded_binary_message) + unpadder.finalize()
        decrypted_binary_message = decrypted_binary_message_bytes.decode()
        decrypted_binary_message= ''.join([chr(int(decrypted_binary_message[i:i+8], 2)) for i in range(0, len(decrypted_binary_message), 8)])

    else: 
        decrypted_binary_message = "".join([chr(int(byte, 2)) for byte in binary_message_bytes])

    message = ''
    for char in decrypted_binary_message:
        if char.isprintable():
            message += char
        else:
            break 
    return message

if __name__ == "__main__":
    original_image = "input.png"
    secret_message = "This is a secret message! with encryption test."
    output_image = "stego_image_encrypted.png"
    encryption_password = "mySecretPassword123"  

    if not os.path.exists(original_image):
        dummy_image = Image.new('RGB', (100, 100), color='red')

        dummy_image.save

