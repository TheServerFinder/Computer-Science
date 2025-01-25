from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter

def image_to_grid_print(image_path, grid_width, grid_height, n_colors=5):
    with Image.open(image_path) as img:
        img = img.convert('RGB')  
        
        # Calculate size of each segment
        segment_width = img.width // grid_width
        segment_height = img.height // grid_height

        color_rows = []
        for i in range(grid_height):
            row_colors = []
            for j in range(grid_width):
                left = j * segment_width
                top = i * segment_height
                right = left + segment_width if j < grid_width - 1 else img.width
                bottom = top + segment_height if i < grid_height - 1 else img.height

                # Crop the image block
                block = img.crop((left, top, right, bottom))
                block_array = np.array(block).reshape(-1, 3)

                if len(set(map(tuple, block_array))) > n_colors:  
                    # Use K-means clustering to reduce colors
                    kmeans = KMeans(n_clusters=n_colors, random_state=0).fit(block_array)
                    labels = kmeans.labels_
                    centers = kmeans.cluster_centers_.astype(np.uint8)
                    block_reduced = centers[labels].reshape(block_array.shape)
                else:
                    block_reduced = block_array  

                # Choose the most common color from the reduced set
                color_counts = Counter(map(tuple, block_reduced))
                chosen_color = max(color_counts, key=color_counts.get)

                hex_color = "#{:02x}{:02x}{:02x}".format(*chosen_color)
                # Format the hex color string with quotes for consistency with your desired output
                row_colors.append(f'"{hex_color}"')

            color_rows.append(row_colors)

        # Print the formatted output
        print("{")
        for row in color_rows:
            print(f'    {{{", ".join(row)}}},')
        print("};")

# Example usage
image_path = 'Umbreon.jpg'
grid_width = 32  # Number of blocks wide    
grid_height = 32  # Number of blocks high
image_to_grid_print(image_path, grid_width, grid_height, n_colors=3)  # Using 3 colors per block