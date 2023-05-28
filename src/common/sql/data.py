from common.sql.moment_sql import get_sql_connection
import os

do_reset_db = False
do_create_schema = False

is_prod = os.environ.get('IS_PROD') # This is a sanity check so we don't accidently reset the DB if it is prod :)

def init_schema():
    schemas = [
        """CREATE TABLE IF NOT EXISTS push_tokens (
            id VARCHAR(255) PRIMARY KEY,
            user_id VARCHAR(255) NOT NULL,
            push_token VARCHAR(255) UNIQUE NOT NULL,
            push_type ENUM('expo') NOT NULL
        );""",
    ]
    return 1


def reset_db():
    if is_prod is True:
        return
    return 1

def init_sql():
    if do_reset_db is True and is_prod is False:
        reset_db()
    if do_create_schema is True:
        init_schema()
    test = 1
