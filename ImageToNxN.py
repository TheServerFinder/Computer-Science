from PIL import Image, ImageDraw, ImageTk
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from tkinter import Tk, Label, Button, Canvas, colorchooser, simpledialog

class VisualEditor:
    def __init__(self, image_path, grid_width, grid_height, n_colors=5):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.n_colors = n_colors
        
        self.original_img = Image.open(image_path).convert('RGB')
        self.segment_width = self.original_img.width // grid_width
        self.segment_height = self.original_img.height // grid_height
        self.hex_grid = self.create_hex_grid()
        
        self.root = Tk()
        self.root.title("Hex Grid Editor")
        self.setup_gui()
    
    def create_hex_grid(self):
        color_rows = []
        for i in range(self.grid_height):
            row_colors = []
            for j in range(self.grid_width):
                left, top = j * self.segment_width, i * self.segment_height
                right = min(left + self.segment_width, self.original_img.width)
                bottom = min(top + self.segment_height, self.original_img.height)
                
                block = self.original_img.crop((left, top, right, bottom))
                block_array = np.array(block).reshape(-1, 3)
                
                if len(set(map(tuple, block_array))) > self.n_colors:  
                    kmeans = KMeans(n_clusters=self.n_colors, random_state=0).fit(block_array)
                    block_reduced = kmeans.cluster_centers_[kmeans.labels_].astype(np.uint8)
                else:
                    block_reduced = block_array  

                color_counts = Counter(map(tuple, block_reduced))
                chosen_color = max(color_counts, key=color_counts.get)
                hex_color = f'#{chosen_color[0]:02x}{chosen_color[1]:02x}{chosen_color[2]:02x}'
                row_colors.append(hex_color)
            color_rows.append(row_colors)
        return color_rows

    def setup_gui(self):
        self.canvas = Canvas(self.root, width=self.grid_width * 20, height=self.grid_height * 20)
        self.canvas.pack()
        self.update_image()
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)  # Bind right-click for color picking
        
        self.color_label = Label(self.root, text="Current Color: ")
        self.color_label.pack()
        
        Button(self.root, text="Print Hex Grid", command=self.print_hex_grid).pack()

    def update_image(self):
        new_img = Image.new('RGB', (self.grid_width * 20, self.grid_height * 20))
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(self.hex_grid):
            for x, color in enumerate(row):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))
        
        self.photo = ImageTk.PhotoImage(new_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    def on_click(self, event):
        x, y = event.x // 20, event.y // 20
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            current_color = self.hex_grid[y][x]
            rgb = tuple(int(current_color[i:i+2], 16) for i in (1, 3, 5))
            self.color_label.config(text=f"Current Color: {current_color} (RGB: {rgb})")
            
            choice = simpledialog.askstring("Color Input", "Enter new hex color (like #RRGGBB):", initialvalue=current_color)
            if choice and len(choice) == 7 and choice[0] == '#':  # Check if valid hex color
                try:
                    # Check if the entered hex is valid
                    int(choice[1:], 16)
                    self.hex_grid[y][x] = choice.upper()
                    self.update_image()
                except ValueError:
                    simpledialog.messagebox.showerror("Error", "Invalid Hex Color. Use format #RRGGBB")
            else:
                # Fallback to color chooser if hex input is not provided or invalid
                new_color = colorchooser.askcolor(color=current_color, title="Choose color")
                if new_color[1]:  # Check if a color was chosen
                    self.hex_grid[y][x] = new_color[1]
                    self.update_image()

    def on_right_click(self, event):
        x, y = event.x // 20, event.y // 20
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            current_color = self.hex_grid[y][x]
            rgb = tuple(int(current_color[i:i+2], 16) for i in (1, 3, 5))
            self.color_label.config(text=f"Color Picked: {current_color} (RGB: {rgb})")

    def print_hex_grid(self):
        print("{")
        for row in self.hex_grid:
            formatted_row = ', '.join([f'"{color}"' for color in row])
            print(f'            {{{formatted_row}}},')
        print("};")

    def run(self):
        self.root.mainloop()

# Example usage
editor = VisualEditor('Cat.jpg', 32, 32, n_colors=3)
editor.run()
