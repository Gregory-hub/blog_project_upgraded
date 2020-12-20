from django.urls import path
from . import views


app_name = 'blog'
urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.log_in, name='login'),
    path('logout/', views.log_out, name='logout'),
    path('sign_up/', views.sign_up, name='sign_up'),
    path('authors/', views.authors, name='authors'),
    path('tags/', views.tags, name='tags'),
    path('tag/<str:tag_name>/', views.tag, name='tag'),
    path('my_page/', views.my_page, name='my_page'),
    path('my_page/<str:article_name>/', views.my_article, name='my_article'),
    path('my_page/<str:article_name>/edit/', views.edit, name='edit'),
    path('my_page/<str:article_name>/delete/', views.delete, name='delete'),
    path('search/', views.search, name='search'),
    path('<str:writer_name>/', views.writer, name='writer'),
    path('<str:writer_name>/<str:article_name>/', views.article, name='article'),
    path('<str:writer_name>/<str:article_name>/report/', views.report, name='report')
]
