from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/(?P<note_id>\d+)/$', consumers.NoteConsumer.as_asgi()),
]
