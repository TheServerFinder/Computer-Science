from PIL import Image, ImageDraw, ImageTk
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from tkinter import Tk, Label, Button, Canvas, colorchooser, simpledialog, messagebox, filedialog, Toplevel, Text, Scrollbar, StringVar, Entry, Frame, IntVar, Checkbutton
import json
import cv2

from PIL import Image, ImageDraw, ImageFilter
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import cv2

def remove_grid(image):
    # Convert image to numpy array for OpenCV operations
    img_array = np.array(image)
    
    # Convert to grayscale for easier edge detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Apply Gaussian blur to reduce noise before edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use Canny Edge Detection to find edges, which should include grid lines
    edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
    
    # Find lines with Hough Line Transform, adjusting parameters for better detection
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=50, minLineLength=30, maxLineGap=5)
    
    if lines is None:
        return image  # No lines detected, return original image

    # Create a mask for lines
    mask = np.zeros_like(img_array)
    for line in lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(mask, (x1, y1), (x2, y2), (255, 255, 255), 2)  # Increased thickness for better coverage

    # Dilate the mask to connect broken lines
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)
    
    # Remove lines from the original image with a stronger inpaint method
    result = cv2.inpaint(img_array, mask[:,:,0], 5, cv2.INPAINT_TELEA)  # Increased radius for inpainting
    
    return Image.fromarray(result)
    gray = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)
    # Apply thresholding to create a binary image
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    
    # Detect lines using Hough Line Transform
    lines = cv2.HoughLinesP(binary, 1, np.pi/180, threshold=200, minLineLength=50, maxLineGap=10)
    
    if lines is None:
        return image  # No lines detected, return original image

    # Create a mask for lines
    mask = np.zeros_like(np.array(image))
    for line in lines:
        x1, y1, x2, y2 = line[0]
        cv2.line(mask, (x1, y1), (x2, y2), (255, 255, 255), 1)

    # Remove lines from the original image
    result = cv2.inpaint(np.array(image), mask[:,:,0], 3, cv2.INPAINT_TELEA)
    return Image.fromarray(result)

def image_to_grid_print(image_path, grid_width, grid_height, n_colors=5):
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        
        # Remove grid if exists
        img = remove_grid(img)
        
        # Resize image to match grid size for better quality
        desired_size = (grid_width * 20, grid_height * 20)
        img = img.resize(desired_size, Image.LANCZOS)

        segment_width = img.width / grid_width
        segment_height = img.height / grid_height

        color_rows = []
        for i in range(grid_height):
            row_colors = []
            for j in range(grid_width):
                left = int(j * segment_width)
                top = int(i * segment_height)
                right = int((j + 1) * segment_width) if j < grid_width - 1 else img.width
                bottom = int((i + 1) * segment_height) if i < grid_height - 1 else img.height

                block = img.crop((left, top, right, bottom))
                block_array = np.array(block).reshape(-1, 3)

                if len(set(map(tuple, block_array))) > n_colors:
                    block_reduced = quantize_colors(block_array, n_colors)
                else:
                    block_reduced = block_array

                color_counts = Counter(map(tuple, block_reduced))
                chosen_color = max(color_counts, key=color_counts.get)

                hex_color = "#{:02x}{:02x}{:02x}".format(*chosen_color)
                row_colors.append(hex_color)

            color_rows.append(row_colors)

        new_img = Image.new('RGB', (grid_width * 20, grid_height * 20))
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(color_rows):
            for x, color in enumerate(row):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))

        return new_img, color_rows

def quantize_colors(block_array, n_colors):
    kmeans = KMeans(n_clusters=n_colors, random_state=0).fit(block_array)
    centroids = kmeans.cluster_centers_.astype(np.uint8)
    labels = kmeans.predict(block_array)
    return centroids[labels]
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        img = img.resize((grid_width * 20, grid_height * 20), Image.LANCZOS)
        
        segment_width = img.width / grid_width
        segment_height = img.height / grid_height

        color_rows = []
        for i in range(grid_height):
            row_colors = []
            for j in range(grid_width):
                left = int(j * segment_width)
                top = int(i * segment_height)
                right = left + 20 if j < grid_width - 1 else img.width
                bottom = top + 20 if i < grid_height - 1 else img.height

                block = img.crop((left, top, right, bottom))
                avg_color = np.mean(np.array(block), axis=(0, 1))
                hex_color = "#{:02x}{:02x}{:02x}".format(int(avg_color[0]), int(avg_color[1]), int(avg_color[2]))
                row_colors.append(hex_color)

            color_rows.append(row_colors)

        new_img = Image.new('RGB', (grid_width * 20, grid_height * 20))
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(color_rows):
            for x, color in enumerate(row):
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))

        return new_img, color_rows
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        
        # Apply dithering to preserve detail
        img = ImageOps.posterize(img, n_colors)
        img = ImageOps.dither(img, 1)
        
        # Resize image to match grid size for better quality
        desired_size = (grid_width * 20, grid_height * 20)
        img = img.resize(desired_size, Image.LANCZOS)

        segment_width = img.width / grid_width
        segment_height = img.height / grid_height

        color_rows = []
        for i in range(grid_height):
            row_colors = []
            for j in range(grid_width):
                left = int(j * segment_width)
                top = int(i * segment_height)
                right = int((j + 1) * segment_width) if j < grid_width - 1 else img.width
                bottom = int((i + 1) * segment_height) if i < grid_height - 1 else img.height

                block = img.crop((left, top, right, bottom))
                block_array = np.array(block).reshape(-1, 3)

                if len(set(map(tuple, block_array))) > n_colors:
                    block_reduced = quantize_colors(block_array, n_colors)
                else:
                    block_reduced = block_array

                color_counts = Counter(map(tuple, block_reduced))
                chosen_color = max(color_counts, key=color_counts.get)

                hex_color = "#{:02x}{:02x}{:02x}".format(*chosen_color)
                row_colors.append(hex_color)

            color_rows.append(row_colors)

        new_img = Image.new('RGB', (grid_width * 20, grid_height * 20))
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(color_rows):
            for x, color in enumerate(row):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))

        return new_img, color_rows

class VisualEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title("Clarks Advanced Pixel Editor")
        self.root.withdraw()
        self.setup_initial_ui()

    def setup_initial_ui(self):
        self.size_window = Toplevel(self.root)
        self.size_window.title("Grid Size")
        self.center_window(self.size_window)
        
        Label(self.size_window, text="Enter grid width:", fg='white', bg='#2B2B2B').grid(row=0, column=0)
        self.width_var = StringVar()
        width_entry = Entry(self.size_window, textvariable=self.width_var, bg='#404040', fg='white')
        width_entry.grid(row=0, column=1)
        Label(self.size_window, text="Enter grid height:", fg='white', bg='#2B2B2B').grid(row=1, column=0)
        self.height_var = StringVar()
        height_entry = Entry(self.size_window, textvariable=self.height_var, bg='#404040', fg='white')
        height_entry.grid(row=1, column=1)
        
        Button(self.size_window, text="Confirm", command=self.confirm_size, fg='white', bg='#2B2B2B').grid(row=2, column=0, columnspan=2)
        
        self.size_window.configure(bg='#2B2B2B')
        self.root.wait_window(self.size_window)

    def confirm_size(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if 1 <= width <= 1000 and 1 <= height <= 1000:
                self.grid_width = width
                self.grid_height = height
                self.n_colors = 5  # Default number of colors for clustering
                
                self.hex_grid = self.create_blank_grid()
                self.setup_gui()
                
                self.draw_color = "#000000"
                self.drawing = False
                self.tool = None
                self.root.deiconify()
            else:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers between 1 and 1000 for width and height.")
        finally:
            self.size_window.destroy()

    def create_blank_grid(self):
        return [["#FFFFFF" for _ in range(self.grid_width)] for _ in range(self.grid_height)]

    def create_blank_grid(self):
        return [["#FFFFFF" for _ in range(self.grid_width)] for _ in range(self.grid_height)]

    def setup_gui(self):
        self.root.configure(bg='#2B2B2B')
        
        border_frame = Frame(self.root, bg='#2B2B2B', padx=40, pady=40)
        border_frame.pack(fill='both', expand=True)
        
        inner_frame = Frame(border_frame, bg='white')
        inner_frame.pack(fill='both', expand=True)
        
        self.canvas = Canvas(inner_frame, width=self.grid_width * 20, height=self.grid_height * 20, bg='white', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        self.update_image()
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B1-Motion>", self.on_draw)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.color_label = Label(self.root, text="Color Picked: ", fg='white', bg='#2B2B2B')
        self.color_label.pack()
        
        control_frame = Frame(self.root, bg='#2B2B2B')
        Button(control_frame, text="Print Hex Grid", command=self.print_hex_grid, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Save Changes", command=self.save_changes, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Load Changes", command=self.load_changes, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Import Image", command=self.import_image, fg='white', bg='#2B2B2B').pack(side="left")
        control_frame.pack()
        
        tool_frame = Frame(self.root, bg='#2B2B2B')
        self.pencil_button = Button(tool_frame, text="Pencil", command=lambda: self.set_tool("pencil"), fg='white', bg='#2B2B2B')
        self.pencil_button.pack(side="left")
        self.erase_button = Button(tool_frame, text="Erase", command=lambda: self.set_tool("erase"), fg='white', bg='#2B2B2B')
        self.erase_button.pack(side="left")
        tool_frame.pack()
        
        color_frame = Frame(self.root, bg='#2B2B2B')
        Button(color_frame, text="Choose Color", command=self.choose_color, fg='white', bg='#2B2B2B').pack(side="left")
        color_frame.pack()

    def update_image(self):
        new_img = Image.new('RGB', (self.grid_width * 20, self.grid_height * 20), color='white')
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(self.hex_grid):
            for x, color in enumerate(row):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b), outline=None)
        
        self.photo = ImageTk.PhotoImage(new_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        # Convert to PhotoImage for Tkinter
        self.photo = ImageTk.PhotoImage(new_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    def on_click(self, event):
        x, y = event.x // 20, event.y // 20
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.current_x, self.current_y = x, y
            if hasattr(self, 'tool') and self.tool == "pencil":
                self.hex_grid[y][x] = self.draw_color
                self.update_image()
            elif hasattr(self, 'tool') and self.tool == "erase":
                self.hex_grid[y][x] = "#FFFFFF"  # Assuming white for erase
                self.update_image()
            else:
                current_color = self.hex_grid[y][x]
                self.open_hex_menu(current_color)

    def on_draw(self, event):
        x, y = event.x // 20, event.y // 20
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            if hasattr(self, 'tool') and self.tool == "pencil":
                self.hex_grid[y][x] = self.draw_color
                self.drawing = True
                self.update_image()
            elif hasattr(self, 'tool') and self.tool == "erase":
                self.hex_grid[y][x] = "#FFFFFF"
                self.drawing = True
                self.update_image()

    def on_release(self, event):
        self.drawing = False

    def set_tool(self, tool):
        if hasattr(self, 'tool') and self.tool == tool:
            # If the tool is already selected, disable it
            self.tool = None
            # Reset button appearance
            if tool == "pencil":
                self.pencil_button.config(bg='#2B2B2B')
            elif tool == "erase":
                self.erase_button.config(bg='#2B2B2B')
        else:
            # Select the tool
            self.tool = tool
            # Change button appearance to indicate selection
            if tool == "pencil":
                self.pencil_button.config(bg='#404040')
                self.erase_button.config(bg='#2B2B2B')
            elif tool == "erase":
                self.erase_button.config(bg='#404040')
                self.pencil_button.config(bg='#2B2B2B')

    def choose_color(self):
        color = colorchooser.askcolor(title="Choose draw color")
        if color[1]:
            self.draw_color = color[1]
            self.color_label.config(text=f"Draw Color: {self.draw_color}")

    def open_hex_menu(self, current_color):
        hex_window = Toplevel(self.root)
        hex_window.title("Hex Color Editor")
        hex_window.geometry("300x150")
        self.center_window(hex_window)
        hex_window.grab_set()
        hex_window.configure(bg='#2B2B2B')

        hex_entry = Entry(hex_window, width=20, bg='#404040', fg='white')
        hex_entry.insert(0, current_color)
        hex_entry.pack(pady=10)

        def confirm_action():
            new_hex = hex_entry.get()
            if len(new_hex) == 7 and new_hex[0] == '#':
                try:
                    int(new_hex[1:], 16)
                    self.hex_grid[self.current_y][self.current_x] = new_hex.upper()
                    self.update_image()
                    hex_window.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Invalid Hex Color. Use format #RRGGBB")
            else:
                messagebox.showerror("Error", "Invalid Hex Color. Use format #RRGGBB")

        def rgb_action():
            hex_window.destroy()
            self.open_rgb_menu(current_color)

        Button(hex_window, text="Confirm", command=confirm_action, fg='white', bg='#2B2B2B').pack(side="left", padx=5)
        Button(hex_window, text="Cancel", command=hex_window.destroy, fg='white', bg='#2B2B2B').pack(side="left", padx=5)
        Button(hex_window, text="RGB ->", command=rgb_action, fg='white', bg='#2B2B2B').pack(side="left", padx=5)

    def open_rgb_menu(self, current_color):
        rgb_window = Toplevel(self.root)
        rgb_window.title("RGB Color Editor")
        rgb_window.geometry("300x150")
        self.center_window(rgb_window)
        rgb_window.grab_set()
        rgb_window.configure(bg='#2B2B2B')
        
        rgb = tuple(int(current_color[i:i+2], 16) for i in (1, 3, 5))
        r_var = StringVar(value=str(rgb[0]))
        g_var = StringVar(value=str(rgb[1]))
        b_var = StringVar(value=str(rgb[2]))
        
        Label(rgb_window, text="R:", fg='white', bg='#2B2B2B').pack()
        r_entry = Entry(rgb_window, textvariable=r_var, bg='#404040', fg='white')
        r_entry.pack()
        Label(rgb_window, text="G:", fg='white', bg='#2B2B2B').pack()
        g_entry = Entry(rgb_window, textvariable=g_var, bg='#404040', fg='white')
        g_entry.pack()
        Label(rgb_window, text="B:", fg='white', bg='#2B2B2B').pack()
        b_entry = Entry(rgb_window, textvariable=b_var, bg='#404040', fg='white')
        b_entry.pack()

        def confirm_action():
            try:
                r, g, b = int(r_var.get()), int(g_var.get()), int(b_var.get())
                if 0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255:
                    new_hex = f'#{r:02x}{g:02x}{b:02x}'.upper()
                    self.hex_grid[self.current_y][self.current_x] = new_hex
                    self.update_image()
                    rgb_window.destroy()
                else:
                    raise ValueError
            except ValueError:
                messagebox.showerror("Error", "Invalid RGB values. Must be between 0 and 255")
        Button(rgb_window, text="Confirm", command=confirm_action, fg='white', bg='#2B2B2B').pack(side="left", padx=5)
        Button(rgb_window, text="Cancel", command=rgb_window.destroy, fg='white', bg='#2B2B2B').pack(side="left", padx=5)

    def on_right_click(self, event):
        x, y = event.x // 20, event.y // 20
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            current_color = self.hex_grid[y][x]
            rgb = tuple(int(current_color[i:i+2], 16) for i in (1, 3, 5))
            self.color_label.config(text=f"Color Picked: {current_color} (RGB: {rgb})")

    def print_hex_grid(self):
        print_window = Toplevel(self.root)
        print_window.title("Hex Grid Output")
        self.center_window(print_window)
        print_window.configure(bg='#2B2B2B')
        
        text = Text(print_window, wrap="none", bg='#404040', fg='white')
        scrollbar = Scrollbar(print_window, command=text.yview)
        text.config(yscrollcommand=scrollbar.set)
        
        text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        text.insert("1.0", "{")
        for row in self.hex_grid:
            formatted_row = '            {' + ', '.join([f'"{color}"' for color in row]) + '},'
            text.insert("end", f"\n{formatted_row}")
        text.insert("end", "\n};")

    def save_changes(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.hex_grid, file)

    def load_changes(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                self.hex_grid = json.load(file)
                self.update_image()

    def import_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            try:
                # Create a new window for color adjustment with consistent styling
                color_adjust_window = Toplevel(self.root)
                color_adjust_window.title("Color Adjustment")
                color_adjust_window.configure(bg='#2B2B2B')  # Match the background color
                self.center_window(color_adjust_window)

                # Label for color count input
                Label(color_adjust_window, text="Enter number of colors:", 
                    fg='white', bg='#2B2B2B').pack(pady=5)

                # Entry for color count with consistent styling
                self.color_count_var = StringVar(value=str(self.n_colors))
                color_count_entry = Entry(color_adjust_window, textvariable=self.color_count_var, 
                                        bg='#404040', fg='white')
                color_count_entry.pack(pady=5)

                def confirm_color_count():
                    try:
                        color_count = int(self.color_count_var.get())
                        if 1 <= color_count <= 256:
                            self.n_colors = color_count
                            print(f"Attempting to process image at path: {file_path}")
                            print(f"Grid dimensions: {self.grid_width}x{self.grid_height}")
                            print(f"Color count: {self.n_colors}")
                            processed_img, self.hex_grid = image_to_grid_print(file_path, self.grid_width, self.grid_height, self.n_colors)
                            self.photo = ImageTk.PhotoImage(processed_img)
                            self.canvas.delete("all")
                            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
                            color_adjust_window.destroy()
                        else:
                            raise ValueError("Color count must be between 1 and 256")
                    except ValueError as e:
                        messagebox.showerror("Error", str(e))

                # Buttons with consistent styling
                Button(color_adjust_window, text="Confirm", command=confirm_color_count, 
                    fg='white', bg='#2B2B2B').pack(side="left", padx=5)
                Button(color_adjust_window, text="Cancel", command=color_adjust_window.destroy, 
                    fg='white', bg='#2B2B2B').pack(side="left", padx=5)

            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to import image: {e}")
    def center_window(self, window):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        window.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()

# Example usage
editor = VisualEditor()
editor.run()
