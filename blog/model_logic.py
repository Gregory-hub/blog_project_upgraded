import os
from PIL import Image

from django.core.files.storage import default_storage
from django.core.files import File
from django.conf import settings
from django.db.models import Model


def delete(instance: Model):
    delete_from_storage(instance)
    instance.image = None
    instance.save()


def delete_from_storage(instance: Model):
    if not instance.image:
        return
    path = instance.image.path
    default_writer_image_path = os.path.join(settings.MEDIA_ROOT, r'writers/images/default.jpg')
    default_tag_image_path = os.path.join(settings.MEDIA_ROOT, r'tags/images/black.jpg')
    if path != default_writer_image_path and path != default_tag_image_path:
        default_storage.delete(path)


def upload_to_storage(file: File, path: str):
    if not os.path.exists(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with open(path, 'wb+') as dest:
        for c in file.chunks():
            dest.write(c)


def resize_image(path: str, square: bool = False):
    image = Image.open(path)
    image.thumbnail((1500, 1500))

    if square:
        image = square_image(image)
    image.save(path)

    return Image.open(path)


def square_image(image: Image):
    width_to_cut = abs(image.width - image.height) / 2

    if image.width > image.height:
        upper, lower = 0, image.height
        left, right = width_to_cut, image.width - width_to_cut
    elif image.height > image.width:
        left, right = 0, image.width
        upper, lower = width_to_cut, image.height - width_to_cut
    else:
        left, upper, right, lower = 0, 0, image.width, image.height

    image = image.crop((left, upper, right, lower))
    return image
