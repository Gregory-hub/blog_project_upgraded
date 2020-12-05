from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib.auth import logout

from . import logic


def index(request):
    index = logic.IndexView(request)
    index.protect_from_unexisting_user()
    index.set_context()
    return index.render()


def article(request, writer_name, article_name):
    article = logic.ArticleView(request)
    article.set_context(writer_name, article_name)

    if request.method == 'GET':
        return article.render()

    if request.method == 'POST':
        return article.process_comment(writer_name, article_name)


def writer(request, writer_name):
    writer = logic.WriterView(request)
    writer.set_context(writer_name)
    return writer.render()


def my_page(request):
    my_page = logic.MyPageView(request)
    if not my_page.user_is_valid():
        return HttpResponse('<h1>401 unauthorized</h1>', status=401)

    if request.method == 'GET':
        my_page.set_context()
        return my_page.render()

    elif request.method == 'POST':
        if 'bio_form' in request.POST:
            return my_page.process_bio_form()
        elif 'add_form' in request.POST:
            return my_page.process_add_form()
        elif 'image_form' in request.POST:
            return my_page.process_image_form()

    else:
        return HttpResponse('<h1>Unsupported Http method</h1>')


def my_article(request, article_name):
    my_article = logic.MyArticleView(request)
    if not my_article.user_is_valid():
        return HttpResponse('<h1>401 unauthorized</h1>', status=401)

    my_article.set_context(article_name)
    return my_article.render()


def edit(request, article_name):
    edit = logic.EditView(request)
    if not edit.user_is_valid():
        return HttpResponse('<h1>401 unauthorized</h1>', status=401)

    if request.method == 'GET':
        edit.set_context(article_name)
        return edit.render()

    elif request.method == 'POST':
        edit.edit_article(article_name)
        return edit.redirect_to_my_article()

    else:
        return HttpResponse('<h1>Unsupported Http method</h1>')


def delete(request, article_name):
    delete = logic.DeleteView(request)
    if not delete.user_is_valid():
        return HttpResponse('<h1>401 unauthorized</h1>', status=401)
    delete.delete(article_name)
    return HttpResponseRedirect(reverse('blog:my_page'))


def log_in(request):
    log_in = logic.LoginView(request)
    if log_in.user_is_valid():
        return HttpResponseRedirect(reverse('blog:index'))

    if request.method == 'GET':
        log_in.set_context()
        return log_in.render()

    elif request.method == 'POST':
        return log_in.log_user_in()

    else:
        return HttpResponse('<h1>Unsupported Http method</h1>')


def sign_up(request):
    sign_up = logic.SignUpView(request)
    if request.method == 'GET':
        sign_up.set_context()
        return sign_up.render()

    elif request.method == 'POST':
        if not sign_up.user_is_valid():
            logout(request)
        return sign_up.create_user_and_writer()

    else:
        return HttpResponse('<h1>Unsupported Http method</h1>')


def log_out(request):
    if request.user.is_authenticated:
        logout(request)

    return HttpResponseRedirect(reverse('blog:index'))


def authors(request):
    authors = logic.AuthorsView(request)
    authors.set_context()
    return authors.render()


def tags(request):
    tags = logic.TagsView(request)
    tags.set_context()
    return tags.render()


def tag(request, tag_name):
    tag = logic.TagView(request)
    tag.set_context(tag_name)
    return tag.render()


def search(request):
    search = logic.SearchView(request)
    search.set_context()
    return search.render()
