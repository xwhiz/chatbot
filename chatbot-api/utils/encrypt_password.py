import bcrypt
from decouple import config


def hash_password(password: str) -> str:
    salt = config("SALT")
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt.encode("utf-8"))
    return hashed.decode("utf-8")
