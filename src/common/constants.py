import os

IS_PROD = os.environ.get('IS_PROD') # This is a sanity check so we don't accidently reset the DB if it is prod :)
