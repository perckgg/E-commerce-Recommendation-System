from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
model = SentenceTransformer('all-MiniLM-L6-v2')

texts = ["Text {}".format(i) for i in range()]

batch_size = 1000
embedding_file = "../data/embeddings.npy"

# Generate embeddings in batches and save them
all_embeddings = []
for i in range(0, len(texts), batch_size):
    batch_texts = texts[i:i+batch_size]
    batch_embeddings = model.encode(batch_texts).astype('float32')
    all_embeddings.append(batch_embeddings)

all_embeddings = np.vstack(all_embeddings)
np.save(embedding_file, all_embeddings)


all_embeddings = np.load(embedding_file)
dimension = all_embeddings.shape[1]

nlist = 100  
quantizer = faiss.IndexFlatL2(dimension) 
index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_L2)

index.train(all_embeddings)

batch_size = 10000
for i in range(0, all_embeddings.shape[0], batch_size):
    batch_embeddings = all_embeddings[i:i+batch_size]
    index.add(batch_embeddings)



# Save the index to disk
faiss.write_index(index, "../data/large_index.ivf")


index = faiss.read_index("../data/large_index.ivf")

# Query example
query = "Example text for search"
query_embedding = model.encode([query]).astype('float32')

# Perform similarity search
k = 10  # Top 10 results
distances, indices = index.search(query_embedding, k)

# Display results
print("Query:", query)
for i in range(k):
    print(f"Result {i+1}:")
    print(f"  Text: {texts[indices[0][i]]}")
    print(f"  Distance: {distances[0][i]}")