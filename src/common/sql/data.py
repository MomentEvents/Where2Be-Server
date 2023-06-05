from common.sql.moment_sql import get_sql_connection
from common.constants import IS_PROD

import os

do_reset_db = False
do_create_schema = False

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
    if IS_PROD is True:
        return
    return 1

def init_sql():
    if do_reset_db is True and IS_PROD is False:
        reset_db()
    if do_create_schema is True:
        init_schema()
    test = 1
