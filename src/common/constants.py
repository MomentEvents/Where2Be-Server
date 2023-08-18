import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

def check_is_prod():
    test = os.environ.get('IS_PROD')
    true_strings = ['true', 'yes', '1', 'on']

    if test.lower() in true_strings:
        return True
    else:
        return False

IS_PROD = check_is_prod() # This is a check to replicate if the server were to be run on prod.
                          # does things such as prevent DB resets, stop logins / signups, and
                          # toggle debug mode

SCRAPER_TOKEN = os.environ.get('SCRAPER_TOKEN')
ENABLE_FIREBASE = True