from Bio.Seq import Seq
import numpy as np

with open("log.txt", "r") as reader:
    for line in reader.readlines():
        seq1 = Seq(line.strip())
        rna = seq1.transcribe()
        print(rna)