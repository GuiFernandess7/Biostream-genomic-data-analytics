import tornado.web
import tornado.websocket
import tornado.ioloop
import aiofiles
import asyncio
import pika
import json

buffer = []

# Conexão com RabbitMQ
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

# Declaração de fila
channel.queue_declare(queue='data-stream')

class WebSocketServer(tornado.websocket.WebSocketHandler):
    """Simple WebSocket handler to serve clients."""

    clients = set()

    def open(self):
        WebSocketServer.clients.add(self)
        print(f"New client connected: {self}")

    def on_close(self):
        WebSocketServer.clients.remove(self)
        print(f"Client disconnected: {self}")

    async def on_message(self, message):
        await self.write_to_file(message)
        await self.send_to_rabbitmq(message)

    async def write_to_file(self, message):
        if isinstance(message, bytes):
            message = message.decode('utf-8')

        async with aiofiles.open("log.txt", mode='a', encoding='utf-8') as f:
            print(f"Message received: {message}")
            await f.write(message + '\n')

    async def send_to_rabbitmq(self, message):
        if isinstance(message, bytes):
            message = message.decode('utf-8')
        channel.basic_publish(exchange='', routing_key='data-stream', body=message)
        print(f"Message sent to RabbitMQ: {message}")

    def on_ping(self, data):
        print("Ping received")
        print(f"Connection made with client: {self}")

    def on_pong(self, data):
        print("Pong received")
        pass

    @classmethod
    async def send_message(cls, message: str):
        for client in cls.clients:
            await client.write_message(message)

class ProcessChannel:
    def __init__(self):
        self.p = 0.72

    def sample(self):
        return "Listening..."

def main():
    app = tornado.web.Application(
        [(r"/websocket/", WebSocketServer)],
        websocket_ping_interval=100,
        websocket_ping_timeout=2000,
    )
    app.listen(8888)

    io_loop = tornado.ioloop.IOLoop.current()

    channel = ProcessChannel()
    periodic_callback = tornado.ioloop.PeriodicCallback(
        lambda: asyncio.create_task(WebSocketServer.send_message(str(channel.sample()))), 100
    )
    periodic_callback.start()

    io_loop.start()

if __name__ == "__main__":
    main()
    print(buffer)
