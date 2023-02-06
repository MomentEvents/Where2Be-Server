import boto3

import base64
from PIL import Image
import json
import cv2
import numpy as np

from io import BytesIO
import io
import secrets


s3 = boto3.client('s3', aws_access_key_id='AKIAR6GV237CVGO4R54X',
    aws_secret_access_key='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')

access_key = 'AKIAR6GV237CVGO4R54X' #'AKIA2IIOOLB6IZ4NQOWM'
secret_access_key = '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' #'YuCZO2+yId3Hj4yBwUXkuIxUiP12100pIH6V6TyW'  #change when putting in py file

# Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id=access_key,
aws_secret_access_key=secret_access_key
)

#Creating S3 Resource From the Session.
s3 = session.resource('s3')

upload_file_bucket =  'moment-events' #test-bucket-chirag5241' #moment-events.s3.us-east-2

def compress_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes))
    width, height = image.size
    resized_image = image
    print("image specs = ",width, height)
    resized_dimensions = image.size
    if width>500:
        percentage = 500 / width
        resized_dimensions = (int(width * percentage), int(height * percentage))
    
    print("resized image specs = ",resized_dimensions)
    resized_image = image.resize(resized_dimensions,Image.ANTIALIAS)
    output_io = io.BytesIO()
    resized_image.save(output_io, format='PNG', optimize=True, quality=85)
    return output_io.getvalue()


async def upload_base64_image(base64_string, directory):
    image_bytes = base64.b64decode(base64_string)

    compressed_image_bytes = compress_image(image_bytes)

    if((directory == None) or (base64_string == None) or (len(directory) == 0) or (len(base64_string) == 0)):
        raise Exception("Empty parameters in upload_base64_image in moment_s3")
    
    if(directory[-1] != '/'):
        directory = directory + '/'
    
    image_id = secrets.token_urlsafe()
    s3.Object(upload_file_bucket, directory+image_id+".png").put(Body=compressed_image_bytes,ContentType='image/PNG')
    event_image = (
        "https://moment-events.s3.us-east-2.amazonaws.com/"+directory+image_id+".png"
    )

    return event_image