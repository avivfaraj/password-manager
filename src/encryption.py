from cryptography.fernet import Fernet, InvalidToken


def encrypt(pwd):
    key, ciphered_text = "",""
    key = Fernet.generate_key()
    # Generate a new key
    try:
        # Define Cipher Suite using the key
        cipher_suite = Fernet(key)

        ciphered_text = cipher_suite.encrypt(str.encode(pwd))
    
    except Exception:
        return "", ""

    return key, ciphered_text

# 2. Return string of date and time
def decrypt(key, _hash):

    # Define Cipher Suite using the key
    cipher_suite = Fernet(key)

    try:
        # Decrypt password
        unciphered_text = str(cipher_suite.decrypt(_hash)).replace('\'','').replace("\"","")
        return unciphered_text[1:]

    except InvalidToken:
        return ""
