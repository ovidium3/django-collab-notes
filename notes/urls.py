from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/signup/", views.signup_view, name="signup"),
    #path("accounts/logout/", views.logout_view.as_view(), name="logout"),
    
    path('', views.note_list, name='note_list'),
    path('create/', views.create_note, name='create_note'),
    path('<int:note_id>/', views.editor, name='editor'),
    path('<int:note_id>/delete/', views.delete_note, name='delete_note'),

    path('api/upload-file/', views.upload_file, name='upload_file'),
    path('api/import-document/', views.import_document, name='import_document'),
    path('api/<int:note_id>/update-content/', views.update_note_content, name='update_note_content'),
]
