from celery_workerv2 import celery
from PIL import Image, ImageOps

@celery.task
def resize_image(image_path, output_path, size):
    with Image.open(image_path) as img:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(output_path)
    return output_path.split('/')[-1]

@celery.task
def crop_image(image_path, output_path, crop_size):
    with Image.open(image_path) as img:
        # Resize and crop to fill the required size
        cropped_img = ImageOps.fit(img, crop_size, Image.Resampling.LANCZOS)
        cropped_img.save(output_path)
    return output_path.split('/')[-1]