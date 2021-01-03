import os

from django.test import TestCase
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings
from django.core.files.storage import default_storage
from django.contrib.auth import get_user

from blog.models import Writer, Article, Comment, Tag
from blog.forms import *


def create_writer(name, age, image=None, bio=None):

    writer = Writer.objects.create(
        name=name,
        age=age,
    )
    if image:
        writer.image = image
    if bio:
        writer.bio = bio
    writer.save()

    return writer


def create_article(writer, name, text, image=None, tag=None):
    article = writer.article_set.create(
        name=name,
        text=text,
        image=image,
        tag=tag,
        pub_date=timezone.now(),
        last_edit=timezone.now()
    )
    return article


def create_tag(name, image=None):
    tag = Tag.objects.create(name=name)
    if image:
        tag.image = image
        tag.save()

    return tag


def create_user(username, password):
    user = User.objects.create_user(username=username, password=password)

    return user


class IndexViewTestCase(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_status_200_with_0_articles(self):
        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)

    def test_status_200_with_1_article(self):
        writer = create_writer('test_writer', 0)
        tag = create_tag('test_tag')
        article = create_article(writer, 'test_article', 'test_article text', tag=tag)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
        article.upload_image(image)

        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)

    def test_status_200_with_2_articles(self):
        writer = create_writer('test_writer', 0)
        tag = create_tag('test_tag')
        for i in range(2):
            article = create_article(writer, 'test_article' + str(i), 'test_article text', tag=tag)
            with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test' + str(i) + '.jpg'), 'rb') as file:
                image = SimpleUploadedFile('test' + str(i) + '.jpg', file.read(), content_type='image/jpg')
            article.upload_image(image)

        response = self.client.get(reverse('blog:index'))
        self.assertEqual(response.status_code, 200)


class ArticleViewTestCase(TestCase):

    def setUp(self):
        self.user = create_user('test_writer', 'test_writer')
        self.writer = create_writer('test_writer', 0)
        self.tag = create_tag('test_tag')
        self.article = create_article(self.writer, 'test_article', 'test_article text', tag=self.tag)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
        self.article.upload_image(image)

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_status_200(self):
        response = self.client.get(reverse('blog:article', args=(self.writer.name, self.article.name)))
        self.assertEqual(response.status_code, 200)

    def test_unexisting_article(self):
        response = self.client.get(reverse('blog:article', args=(self.writer.name, 'random_name')))
        self.assertEqual(response.status_code, 404)

    def test_comment_creation(self):
        username = 'commentator'
        password = 'commentator'

        commentator = create_writer(username, 93)
        create_user(username, password)
        self.client.login(username=username, password=password)

        text = 'test comment text'
        response = self.client.post(
            reverse('blog:article', args=(self.writer.name, self.article.name)),
            {'text': text},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(self.article.comment_set.filter(author=commentator, text=text).exists())


class WriterViewTests(TestCase):

    def setUp(self):
        self.writer = create_writer('test_writer', 31)
        self.tag = create_tag('test_tag')

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_status_200_without_articles(self):
        response = self.client.get(reverse('blog:writer', args=(self.writer.name, )))
        self.assertEqual(response.status_code, 200)

    def test_unexisting_writer(self):
        name = 'test_unexisting'
        response = self.client.get(reverse('blog:writer', args=(name, )))
        self.assertEqual(response.status_code, 404)

    def test_status_200_with_articles(self):
        for i in range(3):
            article = create_article(self.writer, 'test_article' + str(i), 'test_article text', tag=self.tag)
            with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
                image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
            article.upload_image(image)

            response = self.client.get(reverse('blog:writer', args=(self.writer.name, )))
            self.assertEqual(response.status_code, 200)


class MyPageViewTests(TestCase):

    def setUp(self):
        self.tag = create_tag('No tag')
        self.user = create_user('test_writer', 'test_writer')
        self.writer = create_writer('test_writer', 0)
        self.client.login(username='test_writer', password='test_writer')

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_status_200_without_articles(self):
        response = self.client.get(reverse('blog:my_page'))
        self.assertEqual(response.status_code, 200)

    def test_status_200_with_articles(self):
        for i in range(3):
            article = create_article(self.writer, 'test_article' + str(i), 'test_article text', tag=self.tag)
            with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
                image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
            article.upload_image(image)

            response = self.client.get(reverse('blog:my_page'))
            self.assertEqual(response.status_code, 200)

    def test_get_status_if_not_authenticated(self):
        self.client.logout()
        response = self.client.get(reverse('blog:my_page'))
        self.assertEqual(response.status_code, 401)

    def test_post_add_form(self):
        name = 'test_article'
        text = 'test_article text'
        tag = self.tag

        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test1.jpg'), 'rb') as image:
            image = SimpleUploadedFile('test1.jpg', image.read(), content_type='image/jpeg')
            response = self.client.post(reverse('blog:my_page'), {
                'add_form': ['Save'],
                'name': name,
                'text': text,
                'tag': tag.name,
                'image': image,
            })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Article.objects.get(
            author=self.writer,
            name=name,
            text=text,
            tag=tag,
        ).image.path.startswith(os.path.join(settings.MEDIA_ROOT, 'articles/images/test_writer_test_article')))

    def test_post_bio_form(self):
        bio = 'bio'
        age = 54

        response = self.client.post(reverse('blog:my_page'), {
            'bio_form': ['Submit'],
            'bio': bio,
            'age': age,
        })

        writer = Writer.objects.get(name=self.writer.name)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(writer.age, age)
        self.assertEqual(writer.bio, bio)

    def test_post_image_form(self):
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test2.jpg'), 'rb') as image:
            image = SimpleUploadedFile('test2.jpg', image.read(), content_type='image/jpeg')

        response = self.client.post(reverse('blog:my_page'), {
            'image_form': ['Submit'],
            'image': image,
        })

        writer = Writer.objects.get(name=self.writer.name)
        self.assertEquals(response.status_code, 302)
        self.assertTrue(writer.image.path.startswith(os.path.join(settings.MEDIA_ROOT, r'writers/images/test_writer')))


class MyArticleViewTests(TestCase):

    def setUp(self):
        self.tag = create_tag('No tag')
        self.user = create_user('test_writer', 'test_writer')
        self.writer = create_writer('test_writer', 0)
        self.client.login(username='test_writer', password='test_writer')
        self.article = create_article(self.writer, 'test_article', 'test_article text', tag=self.tag)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
        self.article.upload_image(image)

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_status_200(self):
        response = self.client.get(reverse('blog:my_article', args=(self.article.name, )))
        self.assertEqual(response.status_code, 200)

    def test_get_status_if_unauthorized(self):
        self.client.logout()
        response = self.client.get(reverse('blog:my_article', args=(self.article.name, )))
        self.assertEqual(response.status_code, 401)


class EditViewTests(TestCase):

    def setUp(self):
        self.tag = create_tag('test_tag')
        self.user = create_user('test_writer', 'test_writer')
        self.writer = create_writer('test_writer', 0)
        self.client.login(username='test_writer', password='test_writer')
        self.article = create_article(self.writer, 'test_article', 'test_article text', tag=self.tag)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test2.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
        self.article.upload_image(image)

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_response_200(self):
        response = self.client.get(reverse('blog:edit', args=(self.article.name, )))
        self.assertEqual(response.status_code, 200)

    def test_get_response_200_if_unauthorized(self):
        self.client.logout()
        response = self.client.get(reverse('blog:edit', args=(self.article.name, )))
        self.assertEqual(response.status_code, 401)

    def test_post_edits_article_without_image(self):
        new_name = 'test_article_new'
        new_text = 'test_article_new text'
        new_tag = create_tag('No tag')

        response = self.client.post(
            reverse('blog:edit', args=(self.article.name, )), {
                'name': new_name,
                'text': new_text,
                'tag': new_tag.name
            })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Article.objects.get(
            author=self.writer,
            name=new_name,
            text=new_text,
            tag=new_tag,
        ).image.path.startswith(os.path.join(settings.MEDIA_ROOT, r'articles/images/test_writer_test_article_new')))

    def test_post_edits_article_with_image(self):
        new_name = 'test_article_new'
        new_text = 'test_article_new text'
        new_tag = create_tag('No tag')
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test1.jpg'), 'rb') as image:
            new_image = SimpleUploadedFile('test1.jpg', image.read(), content_type='image/jpeg')

        response = self.client.post(
            reverse('blog:edit', args=(self.article.name, )), {
                'name': new_name,
                'text': new_text,
                'tag': new_tag,
                'image': new_image
            })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Article.objects.get(
            author=self.writer,
            name=new_name,
            text=new_text,
            tag=new_tag,
        ).image.path.startswith(os.path.join(settings.MEDIA_ROOT, r'articles/images/test_writer_test_article_new')))


class DeleteViewTests(TestCase):

    def setUp(self):
        self.tag = create_tag('No tag')
        self.user = create_user('test_writer', 'test_writer')
        self.writer = create_writer('test_writer', 0)
        self.client.login(username='test_writer', password='test_writer')
        self.article = create_article(self.writer, 'test_article', 'test_article text', tag=self.tag)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test0.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
        self.article.upload_image(image)

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_deletes_article(self):
        response = self.client.get(reverse('blog:delete', args=(self.article.name, )))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Article.objects.filter(author=self.writer, name=self.article.name).exists())

    def test_get_if_unauthenticated(self):
        client = Client()
        response = client.get(reverse('blog:delete', args=(self.article.name, )))
        self.assertEqual(response.status_code, 401)
        self.assertTrue(Article.objects.filter(author=self.writer, name=self.article.name).exists())


class LogInViewTests(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_response_200(self):
        response = self.client.get(reverse('blog:login'))
        self.assertEqual(response.status_code, 200)

    def test_if_login_post_logs_user_in(self):
        name = 'username'
        password = 'password'

        user = User.objects.create_user(
            username=name,
            password=password
        )

        response = self.client.post(reverse('blog:login'), {'username': name, 'password': password})

        self.assertEqual(response.status_code, 302)
        self.assertTrue(user.is_authenticated)


class SingUpViewTests(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_get_response_200(self):
        response = self.client.get(reverse('blog:sign_up'))
        self.assertEqual(response.status_code, 200)

    def test_if_sign_up_post_creates_user_and_writer(self):
        name = 'username'
        password = 'password'

        response = self.client.post(reverse('blog:sign_up'), {'username': name, 'password': password})

        user = get_user(self.client)

        self.assertTrue(user.is_authenticated)
        self.assertTrue(User.objects.filter(username=name).exists())
        self.assertTrue(Writer.objects.filter(name=name).exists())

        self.assertEquals(response.status_code, 302)


class LogOutViewTests(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_if_logout_post_logs_user_out(self):
        name = 'username'
        password = 'password'

        User.objects.create_user(
            username=name,
            password=password
        )

        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)

        self.client.login(username=name, password=password)

        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)

        response = self.client.get(reverse('blog:logout'))

        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)

        self.assertEquals(response.status_code, 302)


class AuthorsViewTestCase(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_status_200(self):
        response = self.client.get(reverse('blog:authors'))
        self.assertEqual(response.status_code, 200)

        for i in range(20):
            writer_name = 'test_writer' + str(i)
            create_writer(writer_name, i)
            response = self.client.get(reverse('blog:authors'))
            self.assertEqual(response.status_code, 200)


class TagsViewTestCase(TestCase):

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

    def test_status_200(self):
        response = self.client.get(reverse('blog:authors'))
        self.assertEqual(response.status_code, 200)

        for i in range(20):
            tag_name = 'test_tag' + str(i)
            create_tag(tag_name)
            response = self.client.get(reverse('blog:authors'))
            self.assertEqual(response.status_code, 200)


class TagViewTestCase(TestCase):

    def setUp(self):
        self.writer = create_writer('test_writer', 0)
        with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test2.jpg'), 'rb') as file:
            image = SimpleUploadedFile('test_tag.jpg', file.read(), content_type='image/jpg')
        self.tag = create_tag('test_tag', image)

    def tearDown(self):
        for name in default_storage.listdir('articles/images')[1]:
            if name.startswith('test_writer_test_article'):
                default_storage.delete('articles/images/' + name)

        for name in default_storage.listdir('writers/images')[1]:
            if name.startswith('test_writer'):
                default_storage.delete('writers/images/' + name)

        for name in default_storage.listdir('tags/images')[1]:
            if name.startswith('test_tag'):
                default_storage.delete('tags/images/' + name)

    def test_status_200_without_articles(self):
        response = self.client.get(reverse('blog:tag', args=(self.tag.name, )))
        self.assertEqual(response.status_code, 200)

    def test_status_200_with_articles(self):
        # without image
        article = create_article(self.writer, 'test_article0', 'test_article text', tag=self.tag)
        response = self.client.get(reverse('blog:tag', args=(self.tag.name, )))
        self.assertEqual(response.status_code, 200)
        # with image
        for i in range(1, 20):
            name = 'test_article' + str(i)
            article = create_article(self.writer, name, 'test_article text', tag=self.tag)
            with open(os.path.join(settings.MEDIA_ROOT, r'test/images/test' + str(i % 3) + '.jpg'), 'rb') as file:
                image = SimpleUploadedFile('test0.jpg', file.read(), content_type='image/jpg')
            article.upload_image(image)

            response = self.client.get(reverse('blog:tag', args=(self.tag.name, )))
            self.assertEqual(response.status_code, 200)


class ReportViewTestCase(TestCase):
    def setUp(self):
        create_user('reporter', 'password')
        self.reporter = create_writer('reporter', 12)
        self.author = create_writer('author', 11)
        self.article = create_article(self.author, 'article', 'text')

    def test_response_status_if_unauthenticated(self):
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        self.assertEqual(response.status_code, 200)

    def test_response_status_if_authenticated(self):
        self.client.login(username='reporter', password='password')
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        self.assertEqual(response.status_code, 200)

    def test_json_response_if_not_authenticated(self):
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        self.assertEqual(response.json()['ok'], False)
        self.assertEqual(response.json()['message'], 'Not authenticated')

    def test_json_response_if_authenticated(self):
        self.client.login(username='reporter', password='password')
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        print(response.json()['message'])
        self.assertEqual(response.json()['ok'], True)
        self.assertEqual(response.json()['message'], '')

    def test_json_response_if_reported_twice(self):
        self.client.login(username='reporter', password='password')
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        response = self.client.get(reverse('blog:report', args=(self.author.name, self.article.name)))
        self.assertEqual(response.json()['ok'], False)
        self.assertEqual(response.json()['message'], 'You have already reported this article')
