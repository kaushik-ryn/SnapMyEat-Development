from django.urls import re_path,path
from . import consumer


websocket_urlpatterns = [
    # path("ws/orders/<str:restaurant_id>/", consumer.OrderConsumer.as_asgi()),
    # path("ws/waiter/<str:restaurant_id>/", consumer.WaiterCallConsumer.as_asgi()),
    path("ws/live/message/socket/<str:restaurant_id>/", consumer.liveMessageConsumer.as_asgi()),
]
