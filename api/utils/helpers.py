import bcrypt
import string
import datetime
from dateutil import parser
def get_hash_pwd(password):
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def convert_datetime(string: string) -> datetime:
    return parser.parse(string)