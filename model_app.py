from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import faiss
import json
model = SentenceTransformer('all-MiniLM-L6-v2')
index = faiss.read_index("data/large_index.ivf")
with open('app/models/product_name.json', 'r') as json_file:
    product_name = json.load(json_file)
def get_recommend_item(model, query, index, top_item):
    if not query.strip():
        raise ValueError("Query cannot be empty")

    try:
        query_embedding = model.encode([query]).astype('float32')

        distances, indices = index.search(query_embedding, top_item)

        recommended_names = [product_name[idx] for idx in indices[0] if idx < len(product_name)]
        return recommended_names
    except Exception as e:
        raise RuntimeError(f"Error during recommendation: {e}")
app = Flask(__name__)

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    query = data.get('query')
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    try:
        query_embedding = model.encode([query]).astype('float32')

        distances, indices = index.search(query_embedding, top_item)

        recommended_names = [product_name[idx] for idx in indices[0] if idx < len(product_name)]
        return recommended_names
    except Exception as e:
        raise RuntimeError(f"Error during recommendation: {e}")

if __name__=="__main__":
	app.run(host="0.0.0.0", port=7000)