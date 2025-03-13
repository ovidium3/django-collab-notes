from django.urls import path
from . import views

urlpatterns = [
    path('', views.note_list, name='note_list'),
    path('notes/create/', views.create_note, name='create_note'),
    path('notes/<int:note_id>/', views.editor, name='editor'),
]
