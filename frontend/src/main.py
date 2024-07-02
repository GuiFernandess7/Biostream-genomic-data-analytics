import streamlit as st
from Bio import SeqIO
import asyncio
import aio_pika
import plotly.graph_objects as go
from collections import Counter
from Bio import Align
from Bio.Seq import Seq
import traceback
import re

st.set_page_config(page_title="Biostream Dash", page_icon=":bar_chart:", layout="wide")
st.markdown(
    """
    <style>
    .title {
        margin-top: -50px; /* Ajuste a margem superior conforme necessário */
        margin-bottom: 20px; /* Ajuste a margem inferior conforme necessário */
    }
    </style>
    <h2 class="title">📊 🧬 Biostream | Genomic Data Analytics</h2>
    """,
    unsafe_allow_html=True
)

if "sequences" not in st.session_state:
        st.session_state.sequences = []

colors = {
    'A': 'red',
    'T': 'blue',
    'C': 'green',
    'G': 'orange'
}

def validate_websocket_url(url: str):
    websocket_pattern = r"^(ws|wss):\/\/([a-zA-Z0-9\-\.]+)(:\d+)?(\/[^\s]*)?$"
    return re.match(websocket_pattern, url) is not None

def validate_amqp_url(url: str):
    amqp_pattern = r"^amqp:\/\/(?:[^:@\/]+:[^:@\/]+@)?[^:\/]+\.[^:\/]+(:\d+)?(\/[^\s]*)?$"
    return re.match(amqp_pattern, url) is not None

def validate_queue_name(name: str):
    name_pattern = r'^[A-Za-z0-9_-]{1,255}$'

    if re.match(name_pattern, name):
        return True
    else:
        return False

async def consume_messages(address: str, queue_name: str):
    connection = await aio_pika.connect_robust(address)
    try:
        print("Conexão estabelecida com sucesso!")

        channel = await connection.channel()

        queue_name = "data-stream"
        queue = await channel.declare_queue(queue_name)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    body = message.body.decode('utf-8')

                    if body.startswith(">"):
                        st.session_state.sequences.append(body)
                    else:
                        st.session_state.sequences.extend(body)

    except aio_pika.exceptions.AMQPError as e:
        st.error(f"Error: {e}")
        traceback.print_exc()

    except Exception as e:
        st.error(f"Unexpected Error: {e}")
        traceback.print_exc()

    finally:
        if connection:
            await connection.close()

async def show_nucleotide_distribution(graph):
    while True:
        if "sequences" in st.session_state and st.session_state.sequences:
            all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))

            nucleotide_counts = Counter(all_sequences)
            fig_nucleotides = go.Figure()
            for nucleotide, count in nucleotide_counts.items():
                fig_nucleotides.add_trace(go.Bar(x=[nucleotide], y=[count], marker_color=colors.get(nucleotide, 'gray')))
            fig_nucleotides.update_layout(
                title='Nucleotide Distribution',
                xaxis_title='Nucleotide',
                yaxis_title='Count',
                template='plotly_white'
            )


            graph.plotly_chart(fig_nucleotides, use_container_width=True)

        await asyncio.sleep(0.5)

async def dimer_distribution(graph):
    while True:
        if "sequences" in st.session_state and st.session_state.sequences:
            all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))

            dimers = [all_sequences[i:i+2] for i in range(len(all_sequences)-1)]
            dimer_counts = Counter(dimers)
            fig_dimers = go.Figure()
            for dimer, count in dimer_counts.items():
                fig_dimers.add_trace(go.Bar(x=[dimer], y=[count]))
            fig_dimers.update_layout(
                title='Dimer Distribution',
                xaxis_title='Dimer',
                yaxis_title='Count',
                template='plotly_white'
            )

            _, col2 = st.columns(2)
            with col2:
                graph.plotly_chart(fig_dimers, use_container_width=True)

        await asyncio.sleep(0.5)

async def main(address: str = None, queue_name: str = None):
    col1, col2 = st.columns(2)
    with col1:
        graph = st.empty()
    with col2:
        graph2 = st.empty()

    task1 = asyncio.create_task(consume_messages(address, queue_name))
    task2 = asyncio.create_task(show_nucleotide_distribution(graph))
    task3 = asyncio.create_task(dimer_distribution(graph2))
    await asyncio.gather(task1, task2, task3)

if __name__ == '__main__':
    col1, col2 = st.columns([1, 1])
    tab1, tab2 = col1.tabs(["File upload", "Websocket | RabbitMQ"])

    with tab2:
        status = st.empty()
        address = st.text_input("Address")
        st.caption('Examples: [amqp://user:pass@broker.example.com:5672/vhost, amqp://127.0.0.1:5672]')
        queue_name = st.text_input("Queue name")
        start_conn_btt = st.button(label="Run", key="run-addr-button")

    with tab1:
        status = st.empty()
        st.session_state.file = st.file_uploader(label="Upload Genomic Sequence file (FASTA files only).")
        file_check_btt = st.button(label="Run", key="run-file-button")

    if start_conn_btt:
        if not validate_amqp_url(address) and not validate_websocket_url(address):
            st.error("Invalid address")

        if not validate_queue_name(queue_name):
            st.error("Invalid queue name")

        else:
            stop_button = col2.button("Stop", key="stop-button")
            col2.success("Receiving data...")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                asyncio.run(main(address))
                if stop_button:
                    loop.close()
            except KeyboardInterrupt:
                pass
            finally:
                loop.close()
