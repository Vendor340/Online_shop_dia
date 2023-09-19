from hashlib import blake2b
from hmac import compare_digest

KEY_SIZE = 16

def hash_data(data):
    hash_al = blake2b(digest_size=KEY_SIZE)
    data = data.encode("UTF-8")
    hash_al.update(data)
    return hash_al.hexdigest()


def compare_hash(first_hash, second_hash):
    return compare_digest(first_hash, second_hash)
