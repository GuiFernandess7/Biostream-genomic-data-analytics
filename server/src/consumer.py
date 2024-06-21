import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

channel.queue_declare(queue='data-stream')

def callback(ch, method, properties, body):
    message = body.decode('utf-8')
    print(f"Received: {message}")

channel.basic_consume(queue='data-stream', on_message_callback=callback, auto_ack=True)

print('Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
