import os

from django.db.models import Model, ForeignKey, CharField, ImageField, CASCADE, DateTimeField, IntegerField
from django.conf import settings

from . import model_logic


class Article(Model):
    author = ForeignKey('Writer', on_delete=CASCADE)
    name = CharField(max_length=70)
    text = CharField(max_length=100000)
    image = ImageField(max_length=1000, upload_to=r'articles/images', null=True)
    tag = ForeignKey('Tag', on_delete=CASCADE, null=True)
    pub_date = DateTimeField()
    last_edit = DateTimeField()

    def __str__(self):
        return self.name

    def upload_image(self, file):
        os.chdir(settings.MEDIA_ROOT)
        self.delete_image()

        filename = self.author.name + '_' + self.name + '_image' + os.path.splitext(os.path.basename(file.name))[1]
        filename = os.path.join('articles/images/', filename)

        model_logic.upload_to_storage(file, filename)
        model_logic.resize_image(filename, square=True)
        self.image = filename
        self.save()

    def delete_image(self):
        model_logic.delete(self)


class Writer(Model):
    name = CharField(max_length=50)
    bio = CharField(max_length=1000, null=True)
    age = IntegerField(null=True)
    image = ImageField(max_length=1000, upload_to=r'writers/images', default=r'writers/images/default.jpg', null=True)

    def __str__(self):
        return self.name

    def upload_image(self, file):
        os.chdir(settings.MEDIA_ROOT)
        self.delete_image()

        filename = self.name + '_image' + os.path.splitext(os.path.basename(file.name))[1]
        filename = os.path.join('writers/images/', filename)

        model_logic.upload_to_storage(file, filename)
        model_logic.resize_image(filename, square=True)
        self.image = filename
        self.save()

    def delete_image(self):
        model_logic.delete(self)


class Comment(Model):
    article = ForeignKey('Article', on_delete=CASCADE)
    author = ForeignKey('Writer', on_delete=CASCADE)
    text = CharField(max_length=1000)
    comment_date = DateTimeField()

    def __str__(self):
        return self.text


class Tag(Model):
    name = CharField(max_length=70)
    image = ImageField(max_length=1000, upload_to=r'tags/images', default=r'tags/images/black.jpg', null=True)

    def __str__(self):
        return self.name


class Report(Model):
    reporter = ForeignKey('Writer', on_delete=CASCADE)
    article = ForeignKey('Article', on_delete=CASCADE)
