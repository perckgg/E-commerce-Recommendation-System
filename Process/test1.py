import cv2
import os
import numpy as np
import pickle

def compute_and_save_descriptors(image_dir, output_file):
    # Initialize SIFT detector
    sift = cv2.SIFT_create()
    all_descriptors = []
    image_paths = []

    # Process each image in the directory
    for filename in os.listdir(image_dir):
        image_path = os.path.join(image_dir, filename)
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            continue
        # Compute descriptors
        keypoints, descriptors = sift.detectAndCompute(image, None)
        if descriptors is not None:
            all_descriptors.append(descriptors)
            image_paths.append(image_path)

    # Save descriptors and paths
    with open(output_file, 'wb') as f:
        pickle.dump((image_paths, all_descriptors), f)
    print(f"Descriptors saved to {output_file}")

# Precompute descriptors for the dataset
compute_and_save_descriptors("dataset_folder", "descriptors.pkl")

def build_flann_index(descriptors_list):
    # Flatten all descriptors into a single matrix for FLANN
    all_descriptors = np.vstack(descriptors_list)
    index_params = dict(algorithm=1, trees=5)  # KDTree
    flann = cv2.FlannBasedMatcher(index_params, {})
    flann.add([all_descriptors])  # Add descriptors to the FLANN index
    flann.train()
    return flann

def find_top_k_similar(given_image_path, flann, image_paths, descriptors_list, k=5):
    # Initialize SIFT
    sift = cv2.SIFT_create()
    # Read and compute descriptors for the given image
    given_image = cv2.imread(given_image_path, cv2.IMREAD_GRAYSCALE)
    _, given_descriptors = sift.detectAndCompute(given_image, None)
    if given_descriptors is None:
        print("No descriptors found in the query image.")
        return []

    # Perform k-NN search using FLANN
    matches = flann.knnMatch(given_descriptors, k=2)
    good_matches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:  # Lowe's ratio test
            good_matches.append(m)

    # Aggregate scores for each image in the dataset
    scores = {i: 0 for i in range(len(image_paths))}
    for match in good_matches:
        scores[match.imgIdx] += 1

    # Sort images by score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_k = sorted_scores[:k]

    # Return the top-k image paths
    return [(image_paths[i], score) for i, score in top_k]

# Load descriptors and paths
with open("descriptors.pkl", 'rb') as f:
    image_paths, descriptors_list = pickle.load(f)

# Build FLANN index
flann = build_flann_index(descriptors_list)

# Find top-k most similar images
top_k_images = find_top_k_similar("query_image.jpg", flann, image_paths, descriptors_list, k=5)

# Display results
print("Top-k most similar images:")
for rank, (path, score) in enumerate(top_k_images, 1):
    print(f"{rank}: {path} with score {score}")