import streamlit as st
from Bio import SeqIO
import asyncio
import aio_pika
import plotly.graph_objects as go
from collections import Counter
from Bio import Align
from Bio.Seq import Seq

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
st.write('Waiting for messages...')
if "sequences" not in st.session_state:
        st.session_state.sequences = []

colors = {
    'A': 'red',
    'T': 'blue',
    'C': 'green',
    'G': 'orange'
}

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

async def show_nucleotide_distribution(graph): #_and_dimer_distribution(graph):
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

            col1, _ = st.columns(2)
            with col1:
                graph.plotly_chart(fig_nucleotides, use_container_width=True)

        await asyncio.sleep(0.5)

async def dimer_distribution(graph):
    while True:
        if "sequences" in st.session_state and st.session_state.sequences:
            all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))

            # Dimer distribution
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

async def main():
    col1, col2 = st.columns(2)
    with col1:
        graph = st.empty()
    with col2:
        graph2 = st.empty()

    task1 = asyncio.create_task(consume_messages())
    task2 = asyncio.create_task(show_nucleotide_distribution(graph))
    task3 = asyncio.create_task(dimer_distribution(graph2))
    await asyncio.gather(task1, task2, task3)

if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    finally:
        print("Closing Loop")
        loop.close()


""" async def show_trimer_distribution():
    all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))
    trimers = [all_sequences[i:i+3] for i in range(len(all_sequences)-2)]
    trimer_counts = Counter(trimers)
    fig_trimers = go.Figure()
    for trimer, count in trimer_counts.items():
        fig_trimers.add_trace(go.Bar(x=[trimer], y=[count]))
    fig_trimers.update_layout(
        title='Trimer Distribution',
        xaxis_title='Trimer',
        yaxis_title='Count',
        template='plotly_white'
    )
    with empty.container():
        st.plotly_chart(fig_trimers, use_container_width=True)
    await asyncio.sleep(0.5)

async def show_codon_distribution():
    all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">")).replace('T', 'U')
    codons = [all_sequences[i:i+3] for i in range(0, len(all_sequences) - 2, 3)]
    codon_counts = Counter(codons)
    fig_codons = go.Figure()
    for codon, count in codon_counts.items():
        fig_codons.add_trace(go.Bar(x=[codon], y=[count]))
    fig_codons.update_layout(
        title='Codon Distribution',
        xaxis_title='Codon',
        yaxis_title='Count',
        template='plotly_white'
    )
    with empty.container():
        st.plotly_chart(fig_codons, use_container_width=True)
    await asyncio.sleep(0.5)

def get_kmers(sequence, k):
    return [sequence[i:i+k] for i in range(len(sequence) - k + 1)]

async def show_kmer_distribution(k=6):
    all_sequences = ''.join(seq for seq in st.session_state.sequences if not seq.startswith(">"))
    kmers = get_kmers(all_sequences, k)
    kmer_counts = Counter(kmers)
    fig_kmers = go.Figure()
    for kmer, count in kmer_counts.items():
        fig_kmers.add_trace(go.Bar(x=[kmer], y=[count]))
    fig_kmers.update_layout(
        title=f'{k}-mer Distribution',
        xaxis_title=f'{k}-mer',
        yaxis_title='Count',
        template='plotly_white'
    )
    with empty.container():
        st.plotly_chart(fig_kmers, use_container_width=True)
    await asyncio.sleep(0.5)

async def show_variability_analysis(reference_sequence):
    all_sequences = [Seq(seq) for seq in st.session_state.sequences if not seq.startswith(">")]
    aligner = Align.PairwiseAligner()
    aligner.mode = 'global'
    fig_variability = go.Figure()
    for sequence in all_sequences:
        score = aligner.score(reference_sequence, sequence)
        fig_variability.add_trace(go.Scatter(x=[sequence], y=[score], mode='markers'))
    fig_variability.update_layout(
        title='Genetic Variability',
        xaxis_title='Sequence',
        yaxis_title='Alignment Score',
        template='plotly_white'
    )
    with empty.container():
        st.plotly_chart(fig_variability, use_container_width=True)
    await asyncio.sleep(0.5) """
