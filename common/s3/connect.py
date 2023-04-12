import boto3

import base64
from PIL import Image
import json
import cv2
import numpy as np

from io import BytesIO
import io
import secrets
from dotenv import load_dotenv

load_dotenv(dotenv_path='./.env')

S3_URL = os.environ.get('S3_URL')
ACCESS_KEY = os.environ.get('ACCESS_KEY')
SECRET_ACCESS_KEY = os.environ.get('SECRET_ACCESS_KEY')

session = boto3.Session(
aws_access_key_id=ACCESS_KEY,
aws_secret_access_key=SECRET_ACCESS_KEY
)

#Creating S3 Resource From the Session.
s3 = session.resource('s3')

upload_file_bucket =  'moment-events'

def compress_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    resized_image = image
    resized_dimensions = image.size
    if width>500:
        percentage = 500 / width
        resized_dimensions = (int(width * percentage), int(height * percentage))

    resized_image = image.resize(resized_dimensions,Image.ANTIALIAS)
    output_io = io.BytesIO()
    resized_image.save(output_io, format='PNG', optimize=True, quality=85)
    return output_io.getvalue()


async def upload_base64_image(base64_string, directory, file_name):
    image_bytes = base64.b64decode(base64_string)

    try:
        compressed_image_bytes = compress_image(image_bytes)
    except e:
        raise Exception("Unable to compress image")

    if((directory == None) or (base64_string == None) or (len(directory) == 0) or (len(base64_string) == 0)):
        raise Exception("Empty parameters in upload_base64_image in moment_s3")
    
    if(directory[-1] != '/'):
        directory = directory + '/'
    
    s3.Object(upload_file_bucket, directory+file_name+".png").put(Body=compressed_image_bytes,ContentType='image/PNG')
    event_image = (
        S3_URL+directory+file_name+".png"
    )

    return event_image