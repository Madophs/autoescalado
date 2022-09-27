from django.urls import path
from . import views

urlpatterns = [
    path('<int:request_size>/<str:date>/<int:parallelism>/<str:cpu_usage>/<str:memory_usage>/<int:replicas>/<int:retries>', views.index, name='index')
]
