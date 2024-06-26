import streamlit as st
from Bio import SeqIO
import asyncio
import aio_pika
from time import sleep
import plotly.graph_objects as go
from collections import Counter

st.title('Near real time genetic data streaming')
st.write('Waiting for messages...')

async def consume_messages():
    connection = await aio_pika.connect_robust("amqp://guest:guest@localhost/")
    channel = await connection.channel()

    queue = await channel.declare_queue("data-stream")

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                if message.body.decode('utf-8').startswith(">"):
                    st.session_state.sequences.append(message.body.decode('utf-8'))
                else:
                    st.session_state.sequences.extend(message.body.decode('utf-8'))
                await show_data()

empty = st.empty()

async def show_data():
    all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))
    nucleotide_counts = Counter(all_sequences)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=list(nucleotide_counts.keys()), y=list(nucleotide_counts.values())))

    fig.update_layout(
        title='Nucleotide Distribution',
        xaxis_title='Nucleotide',
        yaxis_title='Count',
        template='plotly_white'
    )

    with empty.container():
        st.plotly_chart(fig, use_container_width=True)
    await asyncio.sleep(1)

def main():
    asyncio.run(consume_messages())

if __name__ == '__main__':
    if "sequences" not in st.session_state:
        st.session_state.sequences = []
    main()
