from django.urls import re_path
from core import consumers

websocket_urlpatterns = [
    re_path(r"ws/notifications/$", consumers.NotificationConsumer.as_asgi()),
    re_path(r"ws/course/(?P<course_id>\d+)/$", consumers.CourseConsumer.as_asgi()),
]
