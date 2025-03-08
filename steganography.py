from PIL import Image
import os

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

    # Convert message to binary
    binary_message = ''.join(format(ord(char), '08b') for char in message)
    binary_message += '1111111111111110'

    pixels = list(encoded_image.getdata())
    if len(binary_message) > len(pixels) * 3:
        raise ValueError("Error: Message is too long to be encoded in this image.")

    new_pixels = []
    message_index = 0
    for pixel in pixels:
        new_pixel = list(pixel)
        for i in range(3):
            if message_index < len(binary_message):
                new_pixel[i] = (new_pixel[i] & ~1) | int(binary_message[message_index])
                message_index += 1
        new_pixels.append(tuple(new_pixel))

    encoded_image.putdata(new_pixels)
    try:
        encoded_image.save(output_path, "PNG")
    except Exception as e:
        raise Exception(f"Error: Unable to save encoded image to {output_path}. {e}")
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

    binary_message = ''
    for pixel in pixels:
        for i in range(3):
            binary_message += str(pixel[i] & 1)

    print("Binary message extracted:", binary_message) # ADDED: Print binary message

    end_marker = '1111111111111110'
    end_index = binary_message.find(end_marker)

    if end_index != -1:
        binary_message = binary_message[:end_index]
    else:
        print("⚠️ Warning: No end marker found. Extracted data may be incorrect!")

    print("Binary message after end marker removal:", binary_message) # ADDED: Print binary message after marker removal

    message = ''
    for i in range(0, len(binary_message), 8):
        byte = binary_message[i:i+8]
        if len(byte) == 8:
            char = chr(int(byte, 2))
            if char.isprintable():
                message += char
            else:
                break
    print("Decoded message:", message) # ADDED: Print decoded message
    return message


if __name__ == "__main__":
    original_image = "input.png"
    secret_message = "Hello, this is hidden! This is a longer message to test capacity."
    output_image = "stego_image.png"

    if not os.path.exists(original_image):
        dummy_image = Image.new('RGB', (100, 100), color = 'red')
        dummy_image.save(original_image)
        print(f"Created a dummy {original_image} for testing.")

    try:
        output_path = encode_message(original_image, secret_message, output_image) # Capture output path
        print("Message hidden successfully!")

        extracted_message = decode_message(output_image)
        print("Extracted Message:", extracted_message)

    except FileNotFoundError as e:
        print(e)
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")