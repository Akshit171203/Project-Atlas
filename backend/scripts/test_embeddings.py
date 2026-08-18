import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from app.services.embedding import LocalEmbeddingProvider

def main():
    provider = LocalEmbeddingProvider()

    texts = [
        "What is retrieval augmented generation?",
        "RAG retrieves relevant information before generating an answer.",
        "I like eating pizza.",
    ]

    embeddings = provider.embed(texts)

    print(f"Number of embeddings: {len(embeddings)}")

    for index, embedding in enumerate(embeddings):
        print(
            f"Embedding {index}: {len(embedding)} dimensions"
        )

    # Calculate the similarity as mentioned in the experiment!
    emb_q = np.array(embeddings[0])
    emb_rag = np.array(embeddings[1])
    emb_pizza = np.array(embeddings[2])

    sim_rag = np.dot(emb_q, emb_rag) / (np.linalg.norm(emb_q) * np.linalg.norm(emb_rag))
    sim_pizza = np.dot(emb_q, emb_pizza) / (np.linalg.norm(emb_q) * np.linalg.norm(emb_pizza))

    print(f"\nSimilarity (Question vs RAG): {sim_rag:.4f}")
    print(f"Similarity (Question vs Pizza): {sim_pizza:.4f}")

if __name__ == "__main__":
    main()
