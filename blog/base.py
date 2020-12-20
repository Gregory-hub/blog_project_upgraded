import functools
import logging

from django.http import Http404
from django.http import HttpResponse


logger = logging.getLogger('blog_logger')


def raise_blog_error():
    return HttpResponse('<H1>500\nInternal server error</H1>', status=500)


def base_view(fun):
    @functools.wraps(fun)
    def inner(*args, **kwargs):
        try:
            return fun(*args, **kwargs)
        except Http404:
            raise Http404
        except Exception:
            logger.error('in {fun_name}: 500 server error'.format(fun_name=fun.__module__ + '.' + fun.__name__))
            return raise_blog_error()
    return inner
