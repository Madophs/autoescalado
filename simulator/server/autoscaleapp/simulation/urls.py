from django.urls import path
from . import views

urlpatterns = [
    path('<int:request_size>/<str:date>', views.index, name='index')
]
