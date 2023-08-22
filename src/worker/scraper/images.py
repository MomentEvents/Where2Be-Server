import requests
import numpy as np
import cv2
import base64
import random

from api_connect import get_bucket_url

class Image:
    def __init__(self, url):
        self.url = url
        self.image = None
        self.image_string = None
    
    def process(self):
        try:
            resp = requests.get(self.url, stream=True).raw  # if this works, image exists
        except:
            print("\nNo image!!!\n")
            return False

        resp = requests.get(self.url, stream=True).raw
        image = np.asarray(bytearray(resp.read()), dtype="uint8")

        try:
            image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        except:
            print("Image decode error")
            return False

        if image is None:
            print("\nNO IMAGE HERE!\n")
            return False

        if image.shape[0] < 150 or image.shape[1] < 150:  # If the image is small, resize it
            dim = (image.shape[0] * 4, image.shape[1] * 4)  # new dimensions
            resized = cv2.resize(image, dim, interpolation=cv2.INTER_CUBIC)  # resize image
            resized_blur = cv2.GaussianBlur(resized, (0, 0), cv2.BORDER_DEFAULT)  # blur to remove from image
            image_sharp = cv2.addWeighted(resized, 1.5, resized_blur, -0.6, 0, resized_blur)
            kernel = np.array([[0, -1, 0],
                               [-1, 5, -1],
                               [0, -1, 0]])
            image = cv2.filter2D(src=image_sharp, ddepth=-1, kernel=kernel)
        elif image.shape[1] > 500:
            print("\nLARGE IMAGE\n")
            percentage = 500 / image.shape[1]
            resized_dimensions = (int(image.shape[0] * percentage), int(image.shape[1] * percentage))
            resized = cv2.resize(image, resized_dimensions, interpolation=cv2.INTER_AREA)
            image = resized

        _, buffer = cv2.imencode('.png', image)
        self.image_string = base64.b64encode(buffer).decode()
        self.image = image

        return True

    def get_image_string(self):
        if self.image_string is not None:
            return self.image_string
        elif self.image is not None:
            _, buffer = cv2.imencode('.png', self.image)
            self.image_string = base64.b64encode(buffer).decode()
            return self.image_string
        else:
          return self.get_default_image_string()

    @staticmethod
    def get_default_image_string():
        random_number = str(random.randint(1, 5))
        default_image_url = get_bucket_url() + "app-uploads/images/users/static/default" + random_number + ".png"
        default_image = Image(default_image_url)
        if default_image.process():
            return default_image.get_image_string()
        else:
            return None

