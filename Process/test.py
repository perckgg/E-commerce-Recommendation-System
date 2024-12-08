# import cv2
# import numpy as np
# from sklearn.metrics.pairwise import cosine_similarity
# import requests

# def get_image_from_url(url):
#     response = requests.get(url)
#     if response.status_code != 200:
#         raise ValueError(f"Could not fetch image. Status code: {response.status_code}")

#     image_data = np.asarray(bytearray(response.content), dtype=np.uint8)
#     image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
#     return image

# def compute_descriptors(image, detector):
#     # Detect keypoints and descriptors using SIFT
#     keypoints, descriptors = detector.detectAndCompute(image, None)
#     return keypoints, descriptors

# def calculate_similarity(descriptors1, descriptors2, matcher):
#     # Match descriptors
#     matches = matcher.match(descriptors1, descriptors2)
#     # Sort matches by distance
#     matches = sorted(matches, key=lambda x: x.distance)
#     # Calculate similarity score (e.g., average distance of top matches)
#     if len(matches) > 0:
#         avg_distance = sum(m.distance for m in matches) / len(matches)
#     else:
#         avg_distance = float('inf')  # No matches found
#     return avg_distance

# # Load dataset images
# dataset_images = ['https://m.media-amazon.com/images/I/31UISB90sYL._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/51JFb7FctDL._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/61ZzcguzB1L._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/41O8pnwGG+L._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/41e6oqY5-ZL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/81ZZPvIWnYL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/51PVY5idbhL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/51yB+3-eJwL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/71e1SSUhZeL._AC_UL320_.jpg',
#                ]
# given_image_path = 'https://m.media-amazon.com/images/I/91p5L+GitZL._AC_UL320_.jpg'
# given_image_path = 'https://m.media-amazon.com/images/I/6161gqzzYlL._AC_UL320_.jpg'


# # # Initialize SIFT detector
# # sift = cv2.SIFT_create()

# # # Initialize BFMatcher
# # bf_matcher = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)  # Use NORM_L2 for SIFT

# # # Compute descriptors for the given image
# # given_image = get_image_from_url(given_image_path)
# # _, given_descriptors = compute_descriptors(given_image, sift)

# # # Compute similarity scores with dataset images
# # similarities = []
# # for image_path in dataset_images:
# #     dataset_image = get_image_from_url(image_path)
# #     _, dataset_descriptors = compute_descriptors(dataset_image, sift)
# #     similarity_score = calculate_similarity(given_descriptors, dataset_descriptors, bf_matcher)
# #     similarities.append((image_path, similarity_score))

# # # Sort images by similarity score (ascending order)
# # similarities = sorted(similarities, key=lambda x: x[1])
# # print(similarities)
# # # Get the top-k most similar images
# # k = 2
# # top_k_images = similarities[:k]

# # # Display results
# # print("Top-k most similar images:")
# # for rank, (image_path, score) in enumerate(top_k_images, 1):
# #     print(f"{rank}: {image_path} with score {score:.2f}")
# # cv2.waitKey(0)


# import cv2
# import numpy as np
# from sklearn.cluster import KMeans
# from sklearn.metrics.pairwise import cosine_similarity
# import requests

# # Function to fetch image from URL
# def get_image_from_url(url):
#     response = requests.get(url)
#     if response.status_code != 200:
#         raise ValueError(f"Could not fetch image. Status code: {response.status_code}")
#     image_data = np.asarray(bytearray(response.content), dtype=np.uint8)
#     image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
#     image = cv2.resize(image, (240 , 240))
#     return image

# # Function to compute keypoints and descriptors
# def compute_descriptors(image, detector):
#     keypoints, descriptors = detector.detectAndCompute(image, None)
#     return descriptors

# # Function to build visual words using k-means clustering
# def build_visual_vocabulary(descriptors_list, num_words):
#     all_descriptors = np.vstack(descriptors_list)  # Combine all descriptors from images
#     kmeans = KMeans(n_clusters=num_words, random_state=42)
#     kmeans.fit(all_descriptors)
#     return kmeans

# # Function to represent an image as a histogram of visual words
# def compute_histogram(descriptors, kmeans):
#     words = kmeans.predict(descriptors)
#     print(words)
#     histogram, _ = np.histogram(words, bins=np.arange(kmeans.n_clusters + 1), range=(0, kmeans.n_clusters))
#     return histogram / np.linalg.norm(histogram)

# # Function to compute similarity between histograms
# def calculate_similarity(histogram1, histogram2):
#     # Use cosine similarity to compare histograms
#     return cosine_similarity([histogram1], [histogram2])[0][0]

# # Load dataset images
# dataset_images = ['https://m.media-amazon.com/images/I/31UISB90sYL._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/51JFb7FctDL._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/61ZzcguzB1L._AC_UL320_.jpg', 
#                   'https://m.media-amazon.com/images/I/41O8pnwGG+L._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/41e6oqY5-ZL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/81ZZPvIWnYL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/51PVY5idbhL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/51yB+3-eJwL._AC_UL320_.jpg',
#                   'https://m.media-amazon.com/images/I/71e1SSUhZeL._AC_UL320_.jpg',
#                ]
# given_image_path = 'https://m.media-amazon.com/images/I/91p5L+GitZL._AC_UL320_.jpg'
# given_image_path = 'https://m.media-amazon.com/images/I/6161gqzzYlL._AC_UL320_.jpg'

# # Initialize SIFT detector
# sift = cv2.SIFT_create()

# # List to store descriptors of dataset images
# descriptors_list = []
# for image_path in dataset_images:
#     dataset_image = get_image_from_url(image_path)
#     descriptors = compute_descriptors(dataset_image, sift)
#     descriptors_list.append(descriptors)

# # Build visual vocabulary (set number of visual words)
# num_words = 50  # You can adjust this based on your dataset
# kmeans = build_visual_vocabulary(descriptors_list, num_words)

# # Compute histograms for dataset images
# dataset_histograms = []
# for descriptors in descriptors_list:
#     histogram = compute_histogram(descriptors, kmeans)
#     dataset_histograms.append(histogram)

# # Compute histogram for the given image
# given_image = get_image_from_url(given_image_path)
# given_descriptors = compute_descriptors(given_image, sift)
# given_histogram = compute_histogram(given_descriptors, kmeans)

# # Compute similarity scores with dataset images
# similarities = []
# for i, dataset_histogram in enumerate(dataset_histograms):
#     similarity_score = calculate_similarity(given_histogram, dataset_histogram)
#     similarities.append((dataset_images[i], similarity_score))

# # Sort images by similarity score (descending order)
# similarities = sorted(similarities, key=lambda x: x[1], reverse=True)

# # Get the top-k most similar images
# k = 3
# top_k_images = similarities[:k]

# # Display results
# print("Top-k most similar images:")
# for rank, (image_path, score) in enumerate(top_k_images, 1):
#     print(f"{rank}: {image_path} with score {score:.2f}")

import faiss  # Facebook's FAISS library for ANN
import cv2
import numpy as np
import requests

def get_image_from_url(url):
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Could not fetch image. Status code: {response.status_code}")
    image_data = np.asarray(bytearray(response.content), dtype=np.uint8)
    image = cv2.imdecode(image_data, cv2.IMREAD_COLOR)
    # image = cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
    return image

def compute_descriptors(image, detector):
    keypoints, descriptors = detector.detectAndCompute(image, None)
    return descriptors

def build_visual_vocabulary_faiss(descriptors_list, num_words):
    all_descriptors = np.vstack(descriptors_list).astype('float32')  # Combine all descriptors
    dimension = all_descriptors.shape[1]
    
    kmeans = faiss.Kmeans(d=dimension, k=num_words, verbose=True, gpu=False)
    kmeans.train(all_descriptors)
    return kmeans

def compute_histogram_faiss(descriptors, kmeans):
    _, words = kmeans.index.search(descriptors.astype('float32'), 1)  # Assign descriptors to visual words
    histogram, _ = np.histogram(words, bins=np.arange(kmeans.k + 1), range=(0, kmeans.k))
    return histogram / np.linalg.norm(histogram)  # Normalize histogram

# Load dataset images
dataset_images = [
    'https://m.media-amazon.com/images/I/31UISB90sYL._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/51JFb7FctDL._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/61ZzcguzB1L._AC_UL320_.jpg', 
    'https://m.media-amazon.com/images/I/41O8pnwGG+L._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/41e6oqY5-ZL._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/81ZZPvIWnYL._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/51PVY5idbhL._AC_UL320_.jpg',
    'https://m.media-amazon.com/images/I/71e1SSUhZeL._AC_UL320_.jpg'
    # Add more URLs here...
]
given_image_path = 'https://m.media-amazon.com/images/I/51yB+3-eJwL._AC_UL320_.jpg'

# Initialize SIFT detector
sift = cv2.SIFT_create()

# List to store descriptors of dataset images
descriptors_list = []
for image_path in dataset_images:
    dataset_image = get_image_from_url(image_path)
    descriptors = compute_descriptors(dataset_image, sift)
    descriptors_list.append(descriptors)

# Build visual vocabulary using FAISS
num_words = 100
kmeans = build_visual_vocabulary_faiss(descriptors_list, num_words)

# Compute histograms for dataset images
dataset_histograms = []
for descriptors in descriptors_list:
    histogram = compute_histogram_faiss(descriptors, kmeans)
    dataset_histograms.append(histogram)

# Convert dataset histograms to a NumPy array for FAISS
dataset_histograms_np = np.array(dataset_histograms).astype('float32')

# Build FAISS index for approximate nearest neighbors
dimension = num_words
index = faiss.IndexFlatL2(dimension)  # L2 distance (Euclidean)
index.add(dataset_histograms_np)  # Add dataset histograms to the index

# Compute histogram for the given image
given_image = get_image_from_url(given_image_path)
given_descriptors = compute_descriptors(given_image, sift)
given_histogram = compute_histogram_faiss(given_descriptors, kmeans).astype('float32')

# Query the FAISS index for the top-k most similar images
k = 3
distances, indices = index.search(np.array([given_histogram]), k)

# Display FAISS results
print("Top-k most similar images using FAISS (L2 distance):")
for rank, (idx, distance) in enumerate(zip(indices[0], distances[0]), 1):
    print(f"{rank}: {dataset_images[idx]} with distance {distance:.4f}")



