import tornado.ioloop
import tornado.web
import tornado.websocket
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE,SIG_DFL)


class WebSocketServer(tornado.websocket.WebSocketHandler):
  """Simple WebSocket handler to serve clients."""

  clients = set()

  def open(self):
    WebSocketServer.clients.add(self)

  def on_close(self):
    WebSocketServer.clients.remove(self)

  @classmethod
  def send_message(cls, message: str):
    for client in cls.clients:
      client.write_message(message)

  def on_message(self, message):
    print(f"Recieved: {message}")

  def on_ping(self, data):
    pass

  def on_pong(self, data):
    pass


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
      lambda: WebSocketServer.send_message(str(channel.sample())), 100
  )
  periodic_callback.start()

  io_loop.start()


if __name__ == "__main__":
  main()