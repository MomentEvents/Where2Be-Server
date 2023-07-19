import boto3
import os
import base64
from PIL import Image
import json
import cv2
import numpy as np

from io import BytesIO
import io
import secrets

# Creating Session With Boto3.
session = boto3.Session(
aws_access_key_id=os.environ.get('S3_ACCESS_KEY'),
aws_secret_access_key=os.environ.get('S3_SECRET_ACCESS_KEY')
)

#Creating S3 Resource From the Session.
s3 = session.resource('s3')

upload_file_bucket = os.environ.get('S3_BUCKET') #test-bucket-chirag5241' #moment-events.s3.us-east-2

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
    resized_image = image.resize(resized_dimensions,Image.LANCZOS)
    output_io = io.BytesIO()
    resized_image.save(output_io, format='PNG', optimize=True, quality=85)
    return output_io.getvalue()


async def upload_base64_image(base64_string, directory, file_name):
    image_bytes = base64.b64decode(base64_string)

    compressed_image_bytes = compress_image(image_bytes)

    if((directory == None) or (base64_string == None) or (len(directory) == 0) or (len(base64_string) == 0)):
        raise Exception("Empty parameters in upload_base64_image in moment_s3")
    
    if(directory[-1] != '/'):
        directory = directory + '/'
    
    s3.Object(upload_file_bucket, directory+file_name+".png").put(Body=compressed_image_bytes,ContentType='image/PNG')
    event_image = (
        get_bucket_url()+directory+file_name+".png"
    )

    return event_image

def get_bucket_url():
    return os.environ.get('S3_BUCKET_URL')