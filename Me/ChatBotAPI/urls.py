from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get_response', views.get_chatbot_response, name='chatbot response'),
    path('build', views.build_chatbot, name='build')
]