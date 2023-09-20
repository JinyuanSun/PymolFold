import argparse
from Bio import SeqIO
import time
from cloudmol.cloudmol import PymolFold

def read_fasta(file_path):
    sequences = {}
    for record in SeqIO.parse(file_path, "fasta"):
        sequences[record.id] = str(record.seq)
    return sequences

def predict_structures_from_fasta(fasta_path, save_path='./', method='both'):
    sequences = read_fasta(fasta_path)
    pf = PymolFold()
    pf.set_path(save_path)
    for seq_id, sequence in sequences.items():
        if method == 'esmfold':
            if len(sequence) < 400:
                pf.query_esmfold(sequence, seq_id)
                time.sleep(6)
            else:
                print(f"Sequnece\n\t>{seq_id}\n\t{sequence}\ntoo long, using pymolfold to predict")
                pf.query_pymolfold(sequence=sequence, name=seq_id)
        if method == 'pymolfold':
            pf.query_pymolfold(sequence=sequence, name=seq_id)

def main():
    parser = argparse.ArgumentParser(description='Predict structures for sequences in a FASTA file.')
    parser.add_argument('fasta_path', type=str, help='Path to the FASTA file.')
    parser.add_argument('--save_path', type=str, default='./', help='Path to save results.')
    parser.add_argument('--method', type=str, choices=['esmfold', 'pymolfold'], default='esmfold', 
                        help='Choose prediction method: esmfold or pymolfold.')
    
    args = parser.parse_args()
    predict_structures_from_fasta(args.fasta_path, args.save_path, args.method)

if __name__ == "__main__":
    main()
