from PIL import Image
import numpy as np

def image_to_grid_print(image_path, grid_width, grid_height, image_width, image_height):
    # Open the image
    with Image.open(image_path) as img:
        # Convert image to RGB mode if it's not
        img = img.convert('RGB')
        
        # Resize the image to the specified dimensions, using LANCZOS for better quality
        img = img.resize((image_width, image_height), Image.LANCZOS)  # Changed to LANCZOS for better color preservation

        # Calculate the size of each block
        block_width = image_width // grid_width
        block_height = image_height // grid_height

        # Prepare a list to hold the rows of colors
        color_rows = []

        # Loop through the grid
        for i in range(grid_height):
            row_colors = []  # List to hold colors for the current row
            for j in range(grid_width):
                # Define the boundaries of each block
                left = j * block_width
                top = i * block_height
                right = (j + 1) * block_width if j < grid_width - 1 else image_width
                bottom = (i + 1) * block_height if i < grid_height - 1 else image_height

                # Crop the image to get the block
                block = img.crop((left, top, right, bottom))

                # Convert to numpy array for easier manipulation
                block_array = np.array(block)

                # Calculate median color for better color representation
                median_color = np.median(block_array.reshape(-1, 3), axis=0).astype(np.uint8)

                # Convert median color to hex format, ensuring consistent formatting
                hex_color = "#{:02x}{:02x}{:02x}".format(*median_color)

                # Append the hex color to the current row
                row_colors.append(f'"{hex_color}"')

            # Append the current row to the list of color rows
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
image_width = 695  # Desired width of the image
image_height = 695  # Desired height of the image
image_to_grid_print(image_path, grid_width, grid_height, image_width, image_height)
