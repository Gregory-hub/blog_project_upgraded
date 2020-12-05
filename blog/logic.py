import os
import random
from fuzzysearch import find_near_matches

from django.db.models.query import QuerySet
from django.db.models import Count
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
from django.utils import timezone

from .models import Article, Writer, Tag
from . import forms


class BaseView:
    def render(self):
        return render(self.request, self.template, self.context)

    def user_is_valid(self):
        if not self.request.user.is_authenticated:
            return False
        else:
            return True


class IndexView(BaseView):
    modes_for_1_in_row = [0]
    modes_for_2_in_row = [1, 2, 3]
    modes_for_3_in_row = [4]

    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/blog_index.html'

    def set_context(self):
        article1, groups = self.get_article1_and_groups()
        self.context = {
            'article1': article1,
            'groups': groups,
        }

    def get_article1_and_groups(self):
        articles = Article.objects.order_by('-pub_date')

        if len(articles) > 1:
            article1, groups = self.get_article1_and_groups_if_many_articles(articles)
        elif len(articles) == 1:
            article1, groups = self.get_article1_and_groups_if_one_article(articles)
        else:
            article1, groups = self.get_article1_and_groups_if_no_articles(articles)
        return article1, groups

    def get_article1_and_groups_if_many_articles(self, articles: QuerySet):
        article1 = articles[0]
        articles = articles.exclude(author=article1.author, name=article1.name)
        groups = self.get_groups(articles)
        return article1, groups

    def get_article1_and_groups_if_one_article(self, articles: QuerySet):
        article1 = articles[0]
        groups = []
        return article1, groups

    def get_article1_and_groups_if_no_articles(self, articles: QuerySet):
        article1 = None
        groups = []
        return article1, groups

    def get_groups(self, articles: QuerySet):
        """
        Sorts latest articles by number of comments and groups them by 2 and 3
        Returned list format: [[mode, articles], [mode, articles], ...]
        mode indicates how to display articles in browser
        """
        articles = self.order_articles(articles)
        groups = []
        while len(articles) > 0:
            groups, articles = self.append_to_groups(groups, articles)
        return groups

    def order_articles(self, articles: QuerySet):
        """By number of comments"""
        if len(articles) == 0:
            articles = []
        elif len(articles) == 1:
            articles = list(articles)
        elif len(articles) <= 30:
            articles = articles.annotate(num_comments=Count('comment')).order_by('-num_comments')
        else:
            articles = articles.order_by('-pub_date')[random.randint(20, 30)]
            articles.annotate(num_comments=Count('comment')).order_by('-num_comments')
        return list(articles)

    def append_to_groups(self, groups: list, articles: list):
        if len(articles) <= 4:
            groups, articles = self.append_to_groups_if_few_articles(groups, articles)
            return groups, articles

        modes = self.modes_for_2_in_row + self.modes_for_3_in_row
        mode = random.choice(modes)
        if mode <= 3:
            slice, articles = articles[len(articles) - 2:], articles[:len(articles) - 2]
            groups.append([mode, slice])
        else:
            slice, articles = articles[len(articles) - 3:], articles[:len(articles) - 3]
            groups.append([mode, slice])

        return groups, articles

    def append_to_groups_if_few_articles(self, groups: list, articles: list):
        if len(articles) == 4:
            slice, articles = articles[2:], articles[:2]
            groups.append([random.choice(self.modes_for_2_in_row), slice])
        if len(articles) == 3:
            groups.append([random.choice(self.modes_for_3_in_row), articles])
            articles = []
        elif len(articles) == 2:
            groups.append([random.choice(self.modes_for_2_in_row), articles])
            articles = []
        elif len(articles) == 1:
            groups.append([random.choice(self.modes_for_1_in_row), articles])
            articles = []
        return groups, articles

    def protect_from_unexisting_user(self):
        """In case user(usually superuser) does not exist in Writer db and tries to visit page"""
        user_is_authenticated = self.request.user.is_authenticated
        user_exists = Writer.objects.filter(name=self.request.user.username).exists()
        if user_is_authenticated and not user_exists:
            logout(self.request)


class ArticleView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/article.html'

    def set_context(self, writer_name: str, article_name: str):
        article = self.get_article(writer_name, article_name)
        form = self.get_form()
        recommended_article = self.get_recommended_article(writer_name, article_name)
        comments = article.comment_set.order_by('-comment_date')
        message = self.get_message()

        self.context = {
            'article': article,
            'form': form,
            'recommended_article': recommended_article,
            'comments': comments,
            'message': message,
        }

    def get_article(self, writer_name: str, article_name: str):
        writer = get_object_or_404(Writer, name=writer_name)
        article = get_object_or_404(Article, name=article_name, author=writer)
        return article

    def get_form(self):
        if not self.user_is_valid():
            form = None
        elif self.request.method == 'POST' and 'text' in self.request.POST:
            form = forms.CommentForm(initial={'text': self.request.POST['text']})
        else:
            form = forms.CommentForm()
        return form

    def get_recommended_article(self, writer_name: str, article_name: str):
        writer = get_object_or_404(Writer, name=writer_name)
        article_set = writer.article_set.exclude(name=article_name)

        if article_set.exists():
            recommended_article = article_set.order_by('-pub_date')[0]
        else:
            recommended_article = None

        return recommended_article

    def get_message(self):
        message = None
        if not self.user_is_valid():
            message = 'You cannot comment. Please login'
        elif self.request.method == 'POST':
            form = forms.CommentForm(self.request.POST)
            if not form.is_valid():
                message = 'Form is invalid'
        return message

    def process_comment(self, writer_name: str, article_name: str):
        if not self.request.user.is_authenticated:
            return self.render()

        form = forms.CommentForm(self.request.POST)
        article = self.get_article(writer_name, article_name)

        if form.is_valid():
            self.create_comment(form, article)
            return HttpResponseRedirect(reverse('blog:article', args=(writer_name, article_name)))
        else:
            return self.render()

    def create_comment(self, form: forms.CommentForm, article: Article):
        author = get_object_or_404(Writer, name=self.request.user.username)
        text = form.cleaned_data['text']
        comment_date = timezone.now()

        article.comment_set.create(
            author=author,
            text=text,
            comment_date=comment_date,
        )


class WriterView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/writer.html'

    def set_context(self, writer_name: str):
        writer = get_object_or_404(Writer, name=writer_name)
        articles = writer.article_set.order_by('-pub_date')
        if articles == []:
            message = 'No articles'
        else:
            message = ''

        self.context = {
            'message': message,
            'writer': writer,
            'articles': articles,
        }


class MyPageView(BaseView):
    spec_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/my_page.html'

    def set_context(self, message: str = None, add_form: forms.AddForm = None):
        writer = get_object_or_404(Writer, name=self.request.user.username)
        tags = Tag.objects.all()
        articles = writer.article_set.order_by('-pub_date')

        if message is None and articles == []:
            message = 'No articles'

        image_form = forms.WriterImageForm()
        bio_form = forms.WriterBioForm(initial={'age': writer.age, 'bio': writer.bio})
        if add_form is None:
            add_form = forms.AddForm()

        self.context = {
            'tags': tags,
            'message': message,
            'writer': writer,
            'articles': articles,
            'image_form': image_form,
            'bio_form': bio_form,
            'add_form': add_form,
        }

    def process_bio_form(self):
        writer = Writer.objects.get(name=self.request.user.username)
        bio_form = forms.WriterBioForm(self.request.POST)

        if bio_form.is_valid:
            self.update_writer_age_and_bio(writer)
            return HttpResponseRedirect(reverse('blog:my_page'))
        else:
            message = 'Form is invalid'
            self.set_context(message)
            return self.render()

    def get_age_and_bio(self):
        age = self.request.POST['age']
        bio = self.request.POST['bio']
        if age == '':
            age = None
        if bio == '':
            bio = None
        return age, bio

    def update_writer_age_and_bio(self, writer: Writer):
        age, bio = self.get_age_and_bio()
        writer.age = age
        writer.bio = bio
        writer.save()

    def process_add_form(self):
        add_form = forms.AddForm(self.request.POST, self.request.FILES)
        if not add_form.is_valid():
            return self.render_if_invalid_form()

        text = add_form.cleaned_data['text']
        name = add_form.cleaned_data['name']
        writer = Writer.objects.get(name=self.request.user.username)

        if self.spec_chars_in_name(name):
            return self.render_if_spec_chars_in_name()
        if not self.name_length_is_ok(name):
            return self.render_if_name_or_text_too_long('name', name, text)
        if not self.text_length_is_ok(text):
            return self.render_if_name_or_text_too_long('text', name, text)

        if list(writer.article_set.filter(name=name)) != []:
            return self.render_if_name_is_unavailable()

        self.create_article()

        return HttpResponseRedirect(reverse('blog:my_page'))

    def render_if_invalid_form(self):
        message = 'Form is invalid'
        self.set_context(message)
        return self.render()

    def spec_chars_in_name(self, name: str):
        for char in self.spec_chars:
            if char in name:
                return True
        return False

    def render_if_spec_chars_in_name(self, text: str):
        message = 'Name cannot contain special characters: {}'.format(', '.join(self.spec_chars))
        add_form_with_init = forms.AddForm(initial={'text': text})
        self.set_context(message, add_form_with_init)
        return self.render()

    def name_length_is_ok(self, name: str):
        max_name_length = Article._meta.get_field('name').max_length
        if len(name) >= max_name_length:
            return False
        return True

    def text_length_is_ok(self, text: str):
        max_text_length = Article._meta.get_field('text').max_length
        if len(text) >= max_text_length:
            return False
        return True

    def render_if_name_or_text_too_long(self, too_long: str, name: str, text: str):
        message = '{} is too long'.format(too_long)
        add_form_with_init = forms.AddForm(initial={'name': name, 'text': text})
        self.set_context(message, add_form_with_init)
        return self.render()

    def render_if_name_is_unavailable(self):
        message = 'This name is not available'
        self.set_context(message)
        return self.render()

    def create_article(self):
        tag_name = self.request.POST['tag']
        tag = get_object_or_404(Tag, name=tag_name)
        text = self.request.POST['text']
        name = self.request.POST['name']
        writer = Writer.objects.get(name=self.request.user.username)

        article = writer.article_set.create(
            name=name,
            text=text,
            tag=tag,
            pub_date=timezone.now(),
            last_edit=timezone.now(),
        )
        article.upload_image(self.request.FILES['image'])

    def process_image_form(self):
        writer = Writer.objects.get(name=self.request.user.username)
        image_form = forms.WriterImageForm(self.request.POST, self.request.FILES)
        if not image_form.is_valid():
            return self.render_if_invalid_form()
        self.replace_image(writer)
        return HttpResponseRedirect(reverse('blog:my_page'))

    def replace_image(self, writer: Writer):
        writer.delete_image()
        writer.upload_image(self.request.FILES['image'])


class MyArticleView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/my_article.html'

    def set_context(self, article_name: str):
        writer = get_object_or_404(Writer, name=self.request.user.username)
        article = writer.article_set.get(name=article_name)
        self.context = {
            'article': article,
            'comments': article.comment_set.order_by('-comment_date'),
        }


class EditView(BaseView):
    spec_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']

    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/edit.html'

    def set_context(self, article_name: str, message: str = None):
        writer = get_object_or_404(Writer, name=self.request.user.username)
        article = get_object_or_404(Article, name=article_name, author=writer)

        form = forms.EditForm(initial={
            'name': article.name,
            'text': article.text,
            'tag': article.tag,
        })

        self.context = {
            'tags': Tag.objects.all(),
            'article': article,
            'message': message,
            'form': form,
        }

    def edit_article(self, article_name: str):
        form = forms.EditForm(self.request.POST, self.request.FILES)
        if not form.is_valid():
            return self.render_if_invalid_form()

        text = form.cleaned_data['text']
        name = form.cleaned_data['name']
        writer = get_object_or_404(Writer, name=self.request.user.username)
        article = get_object_or_404(Article, name=article_name, author=writer)

        if self.spec_chars_in_name(name):
            return self.render_if_spec_chars_in_name()
        if not self.name_length_is_ok(name):
            return self.render_if_name_or_text_too_long('name', name, text)
        if not self.text_length_is_ok(text):
            return self.render_if_name_or_text_too_long('text', name, text)

        if name != article_name and list(writer.article_set.filter(name=name)) != []:
            return self.render_if_name_is_unavailable()

        self.update_article(article)

    def render_if_invalid_form(self):
        message = 'Form is invalid'
        self.set_context(message)
        return self.render()

    def spec_chars_in_name(self, name: str):
        for char in self.spec_chars:
            if char in name:
                return True
        return False

    def render_if_spec_chars_in_name(self, text: str):
        message = 'Name cannot contain special characters: {}'.format(', '.join(self.spec_chars))
        add_form_with_init = forms.AddForm(initial={'text': text})
        self.set_context(message, add_form_with_init)
        return self.render()

    def name_length_is_ok(self, name: str):
        max_name_length = Article._meta.get_field('name').max_length
        if len(name) >= max_name_length:
            return False
        return True

    def text_length_is_ok(self, text: str):
        max_text_length = Article._meta.get_field('text').max_length
        if len(text) >= max_text_length:
            return False
        return True

    def render_if_name_or_text_too_long(self, too_long: str, name: str, text: str):
        message = '{} is too long'.format(too_long)
        add_form_with_init = forms.AddForm(initial={'name': name, 'text': text})
        self.set_context(message, add_form_with_init)
        return self.render()

    def render_if_name_is_unavailable(self):
        message = 'This name is not available'
        self.set_context(message)
        return self.render()

    def update_article(self, article: Article):
        old_name = article.name
        article.name = self.request.POST['name']
        article.text = self.request.POST['text']
        tag = get_object_or_404(Tag, name=self.request.POST['tag'])
        article.tag = tag
        article.last_edit = timezone.now()

        if article.name != old_name and 'image' not in self.request.FILES:
            self.rename_image(article)

        article.save()
        self.upload_image(article)

    def rename_image(self, article: Article):
        if article.image:
            old = article.image.path
        else:
            old = None

        dirname = os.path.join(settings.MEDIA_ROOT, 'articles/images')
        ext = os.path.splitext(article.image.path)[1]
        new_image_name = article.author.name + '_' + article.name + ext
        new = os.path.join(dirname, new_image_name)

        if os.path.exists(old):
            os.rename(old, new)
        article.image = 'articles/images/' + new_image_name

    def upload_image(self, article: Article):
        if 'image' in self.request.FILES:
            image = self.request.FILES['image']
            article.upload_image(image)

    def redirect_to_my_article(self):
        author_name = self.request.user.username
        article_name = self.request.POST['name']
        writer = Writer.objects.get(name=author_name)
        article = writer.article_set.get(name=article_name)
        return HttpResponseRedirect(reverse('blog:my_article', args=(article.name, )))


class DeleteView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request

    def delete(self, article_name: str):
        writer = Writer.objects.get(name=self.request.user.username)
        article = writer.article_set.get(name=article_name)
        article.delete_image()
        article.delete()


class LoginView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/login.html'

    def set_context(self, message: str = None):
        form = forms.LogInForm()
        self.context = {
            'form': form,
            'message': message
        }

    def log_user_in(self):
        form = forms.LogInForm(self.request.POST)
        if not form.is_valid():
            message = 'Form is invalid'
            self.set_context(message)
            return self.render()

        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user)
            return HttpResponseRedirect(reverse('blog:index'))
        else:
            if list(User.objects.filter(username=username)) == []:
                message = 'User does not exist'
                self.set_context(message)
                return self.render()
            else:
                message = 'Wrong password'
                self.set_context(message)
                return self.render()


class SignUpView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/sign_up.html'

    def set_context(self, message: str = None):
        form = forms.SignUpForm()
        self.context = {
            'form': form,
            'message': message
        }

    def create_user_and_writer(self):
        form = forms.SignUpForm(self.request.POST)
        if not form.is_valid():
            message = 'Form is invalid'
            self.set_context(message)
            return self.render()

        writer_success = self.create_writer()
        if not writer_success:
            return self.name_is_invalid()

        user_success = self.create_user()
        if not user_success:
            return self.name_is_invalid()

        return HttpResponseRedirect(reverse('blog:my_page'))

    def create_writer(self):
        name = self.request.POST['username']
        if list(Writer.objects.filter(name=name)) == []:
            Writer.objects.create(name=name)
            return True
        else:
            return False

    def create_user(self):
        username = self.request.POST['username']
        password = self.request.POST['password']

        if list(User.objects.filter(username=username)) == []:
            self.create_user_and_login(username, password)
            return True
        else:
            return False

    def name_is_invalid(self):
        message = "This name is occupied"
        self.set_context(message)
        return self.render()

    def create_user_and_login(self, username: str, password: str):
        User.objects.create_user(username=username, password=password)
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)


class AuthorsView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/authors.html'

    def set_context(self):
        writers = Writer.objects.annotate(num_articles=Count('article')).order_by('-num_articles')
        self.context = {
            'writers': writers,
        }


class TagsView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/tags.html'

    def set_context(self):
        tags, top_tags = self.get_tags_and_top_tags()
        self.context = {
            'tags': tags,
            'top_tags': top_tags
        }

    def get_tags_and_top_tags(self):
        tags = list(Tag.objects.annotate(num_articles=Count('article')).order_by('-num_articles'))
        if len(tags) == 0:
            top_tags, tags = None, None
        elif 1 <= len(tags) <= 3:
            top_tags, tags = tags, None
        else:
            top_tags, tags = tags[:3], tags[3:]
        return tags, top_tags


class TagView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/tag.html'

    def set_context(self, tag_name: str):
        tag = Tag.objects.get(name=tag_name)
        articles = tag.article_set.order_by('-pub_date')

        self.context = {
            'tag': tag,
            'articles': articles,
        }


class SearchView(BaseView):
    def __init__(self, request: WSGIRequest):
        self.request = request
        self.template = 'blog/search.html'

    def set_context(self):
        q = self.request.GET.get('q')
        if len(q) == 0:
            return HttpResponseRedirect(reverse('blog:index'))

        articles = self.search_in(Article.objects.all(), q)
        writers = self.search_in(Writer.objects.all(), q)
        tags = self.search_in(Tag.objects.all(), q)

        self.context = {
            'articles': articles,
            'writers': writers,
            'tags': tags
        }

    def search_in(self, sequence, q):
        sequence = list(sequence)
        l_dist = len(q) // 4

        result = []
        for instance in sequence:
            inst_name_field = instance.name
            if find_near_matches(q, inst_name_field, max_l_dist=l_dist) != []:
                result.append(instance)

        if len(result) == 0:
            return None
        return result
