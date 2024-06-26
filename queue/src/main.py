"""Not Implemented"""

import asyncio
import aio_pika

async def consume_messages():
    seqs = {}
    current_seq_id = None
    current_sequence = []

    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()

    queue = await channel.declare_queue("data-stream")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                line = message.body.decode('utf-8')

                if line.startswith(">"):
                    if current_seq_id is not None:
                        seqs[current_seq_id] = "".join(current_sequence)
                    current_seq_id = line.strip()
                    current_sequence = []
                else:
                    current_sequence.append(line.strip())

        if current_seq_id is not None:
            seqs[current_seq_id] = "".join(current_sequence)

    print(seqs)
    await connection.close()

def main():
    asyncio.run(consume_messages())

if __name__ == '__main__':
    main()
