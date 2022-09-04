from django.urls import path
from . import views

urlpatterns = [
    path('<int:request_size>/', views.index, name='index')
]
