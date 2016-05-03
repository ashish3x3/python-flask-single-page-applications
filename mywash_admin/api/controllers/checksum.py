import base64
import string
import random
import hashlib

from Crypto.Cipher import AES


IV = "@@@@&&&&####$$$$"
BLOCK_SIZE = 16


def generate_checksum(param_dict, merchant_key, salt=None):
    try:
        params_string = __get_param_string__(param_dict)
        salt = salt if salt else __id_generator__(4)
        final_string = '%s|%s' % (params_string, salt)

        hasher = hashlib.sha256(final_string.encode())
        hash_string = hasher.hexdigest()

        hash_string += salt

        return __encode__(hash_string, IV, merchant_key)
    except Exception as e:
        print "generate_checksum()", str(e)
        return {"status": "failure", "error": str(e)}


def verify_checksum(param_dict, merchant_key, checksum):
    try:
        # Remove checksum
        if 'CHECKSUMHASH' in param_dict:
            param_dict.pop('CHECKSUMHASH')

        # Get salt
        paytm_hash = __decode__(checksum, IV, merchant_key)
        salt = paytm_hash[-4:]
        calculated_checksum = generate_checksum(param_dict, merchant_key, salt=salt)
        return calculated_checksum == checksum
    except Exception as e:
        print "verify_checksum()", str(e)
        return {"status": "failure", "error": str(e)}


def __id_generator__(size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    try:
        return ''.join(random.choice(chars) for _ in range(size))
    except Exception as e:
        print "__id_generator__()", str(e)
        return {"status": "failure", "error": str(e)}


def __get_param_string__(params):
    params_string = []
    try:
        for key in sorted(params.iterkeys()):
            value = params[key]
            params_string.append('' if value == 'null' else str(value))
        return '|'.join(params_string)
    except Exception as e:
        print "__get_param_string__()", str(e)
        return {"status": "failure", "error": str(e)}


__pad__ = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * chr(BLOCK_SIZE - len(s) % BLOCK_SIZE)
__unpad__ = lambda s: s[0:-ord(s[-1])]


def __encode__(to_encode, iv, key):
    try:
        # Pad
        to_encode = __pad__(to_encode)
        # Encrypt
        c = AES.new(key, AES.MODE_CBC, iv)
        to_encode = c.encrypt(to_encode)
        # Encode
        to_encode = base64.b64encode(to_encode)
        return to_encode
    except Exception as e:
        print "__encode__()", str(e)
        return {"status": "failure", "error": str(e)}


def __decode__(to_decode, iv, key):
    try:
        # Decode
        print "Decode"
        to_decode = base64.b64decode(to_decode)
        print "Decrypt"
        # Decrypt
        c = AES.new(key, AES.MODE_CBC, iv)
        to_decode = c.decrypt(to_decode)
        print "Pad"
        # remove pad
        return __unpad__(to_decode)
    except Exception as e:
        print "__decode__()", str(e)
        return {"status": "failure", "error": str(e)}


def validate(param_dict, merchant_key):
    try:
        if 'CHECKSUMHASH' not in param_dict:
            return False
        checksum = param_dict.pop('CHECKSUMHASH')
        print checksum
        return verify_checksum(param_dict, merchant_key, checksum)
    except Exception as e:
        print "validate()", str(e)
        return {"status": "failure", "error": str(e)}
