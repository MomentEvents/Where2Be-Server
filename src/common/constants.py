import os

def check_is_prod():
    test = os.environ.get('IS_PROD')
    true_strings = ['true', 'yes', '1', 'on']

    if test.lower() in true_strings:
        return True
    else:
        return False

IS_PROD = check_is_prod() # This is a sanity check so we don't accidently reset the DB if it is prod :)