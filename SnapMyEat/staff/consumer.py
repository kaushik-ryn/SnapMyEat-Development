import json
from channels.generic.websocket import AsyncWebsocketConsumer 

# consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class liveMessageConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.order_group = f"restaurant_{self.restaurant_id}_orders"
        self.waiter_group = f"restaurant_{self.restaurant_id}_waiter"

        try:
            # Join both groups
            await self.channel_layer.group_add(self.order_group, self.channel_name)
            await self.channel_layer.group_add(self.waiter_group, self.channel_name)
            await self.accept()

            print(f"[WS] Connected to groups: {self.order_group}, {self.waiter_group}")

            await self.send(text_data=json.dumps({
                "type": "hello_combined",
                "message": "Connected to order + waiter socket"
            }))
        except Exception as e:
            print(f"[WS] Connection error: {e}")
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.order_group, self.channel_name)
        await self.channel_layer.group_discard(self.waiter_group, self.channel_name)
        print(f"[WS] Disconnected from {self.order_group} & {self.waiter_group}")

    async def receive(self, text_data):
        print(f"[WS] Received data: {text_data}")

    # Triggered on order group broadcast
    async def send_order_notification(self, event):
        print(f"[WS] Sending order notification: {event}")
        await self.send(text_data=json.dumps({
            "type": "order_notification",
            "order": event["order"]
        }))

    # Triggered on waiter group broadcast
    async def waiter_call(self, event):
        print(f"[WS] Sending waiter call: {event}")
        await self.send(text_data=json.dumps({
            "type": "waiter_notification",
            "table": event["table"]
        }))
        print("snt")


"""
class OrderConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"[WS] New connection for restaurant: {self.scope['url_route']['kwargs']['restaurant_id']}")
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.group_name = f"restaurant_{self.restaurant_id}_orders"

        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"[WS] Connection accepted for group: {self.group_name}")
        except Exception as e:
            print(f"[WS] Error during connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        print(f"[WS] Disconnected from group: {self.group_name} with code: {close_code}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        print(f"[WS] Received data: {text_data}")
        # You can handle receiving messages from frontend if needed
        pass

    async def send_order_notification(self, event):
        print(f"[WS] Sending order notification: {event}")
        await self.send(text_data=json.dumps({
            "order": event["order"]
        }))


class WaiterCallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
        self.group_name = f"restaurant_{self.restaurant_id}_waiter"
        try:
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()
            print(f"[WS] Connection accepted for group: {self.group_name}")
            await self.send(text_data=json.dumps({
                "type": "hello_waiter",
                "message": "Waiter socket connected!"
            }))
        except Exception as e:
            print(f"[WS] Error during connect: {e}")
            await self.close()

    async def disconnect(self, close_code):
        print(f"[WS] Disconnected from group: {self.group_name} with code: {close_code}")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Receive event from client
    async def receive(self, text_data):
        print(f"[WS] Received data: {text_data}")
        data = json.loads(text_data)
        table_no = data.get("table")

        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "waiter.call",
                "table": table_no
            }
        )
        print("send")

    # Send to group
    async def waiter_call(self, event):
        print(f"[WS] Sending waiter call: {event}")
        await self.send(text_data=json.dumps({
            "type": "waiter_call",
            "table": event["table"]
        }))
        print("sent")


"""