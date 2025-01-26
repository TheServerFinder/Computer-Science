from PIL import Image, ImageDraw, ImageTk
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from tkinter import Tk, Toplevel, Menu, Label, Button, Canvas, colorchooser, simpledialog, messagebox, filedialog, Text, StringVar, Entry, Frame, IntVar, Checkbutton, LEFT, BOTTOM, RIGHT, X, Y, BOTH, Scale, Listbox, HORIZONTAL, END, ttk
import json
import cv2

def remove_grid(image):
    # Convert image to numpy array for OpenCV operations
    img_array = np.array(image)
    
    # Convert to grayscale for easier edge detection
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Apply Gaussian blur to reduce noise before edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Use Canny Edge Detection to find edges, which should include grid lines
    edges = cv2.Canny(blurred, 50, 150, apertureSize=7)
    
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

def image_to_grid_print(image_path, grid_width, grid_height, n_colors=5):
    with Image.open(image_path) as img:
        img = img.convert('RGB')
        
        # Remove grid if exists
        img = remove_grid(img)
        
        # Resize image to match grid size for better quality, using LANCZOS
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

class VisualEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title("Clarks Advanced Pixel Editor")
        self.root.resizable(True, True)
        self.zoom_scale = 1.0
        self.zoom_speed = 0.1
        self.undo_stack = []
        self.redo_stack = []
        self.layers = []  # Initialize as empty list
        self.current_layer = 0

        self.root.withdraw()
        self.setup_menu()
        self.setup_initial_ui()


    def setup_menu(self):
        menubar = Menu(self.root)
        filemenu = Menu(menubar, tearoff=0)
        filemenu.add_command(label="New", command=self.new_project)
        filemenu.add_command(label="Print Hex Grid", command=self.print_hex_grid)
        filemenu.add_command(label="Load Image", command=self.import_image)
        filemenu.add_command(label="Save Image", command=self.save_image)
        filemenu.add_command(label="Load JSON", command=self.load_changes)
        filemenu.add_command(label="Save JSON", command=self.save_changes)
        menubar.add_cascade(label="File", menu=filemenu)
        
        self.root.config(menu=menubar)
        
    def new_project(self):
        # This method would reset the editor to a new state
        self.root.withdraw()
        self.setup_initial_ui()  # This would prompt for new grid size
        self.root.deiconify()

    def open_project(self):
        # This method would open a previously saved project
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                self.layers = json.load(file)
                # Assuming the loaded data is structured as a list of layers
                self.current_layer = 0
                self.update_image()

    def export_image(self):
        # This method would handle exporting the image in different formats
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("GIF files", "*.gif")])
        if file_path:
            combined_grid = self.combine_layers()
            current_image = Image.new('RGB', (self.grid_width * 20, self.grid_height * 20))
            draw = ImageDraw.Draw(current_image)
            for y, row in enumerate(combined_grid):
                for x, color in enumerate(row):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))
            
            if file_path.endswith('.png'):
                current_image.save(file_path, "PNG")
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                quality = simpledialog.askinteger("Quality", "Enter JPEG quality (1-95):", minvalue=1, maxvalue=95, initialvalue=90)
                if quality:
                    current_image.save(file_path, "JPEG", quality=quality)
            elif file_path.endswith('.gif'):
                current_image.save(file_path, "GIF")


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

    def on_mousewheel(self, event):
        # Adjust zoom based on mouse wheel scroll
        old_scale = self.zoom_scale
        if event.delta > 0:
            self.zoom_scale += self.zoom_speed
        else:
            self.zoom_scale = max(0.1, self.zoom_scale - self.zoom_speed)  # Prevent zoom scale from going to zero
        
        # Update canvas size based on new zoom level
        max_size = 800
        canvas_width = min(int(self.grid_width * 20 * self.zoom_scale), max_size)
        canvas_height = min(int(self.grid_height * 20 * self.zoom_scale), max_size)
        self.canvas.config(width=canvas_width, height=canvas_height)

        # Center zoom on mouse position
        x, y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        scale_factor = self.zoom_scale / old_scale
        self.canvas.scale("all", x, y, scale_factor, scale_factor)
        self.update_image()


    def save_image(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")])
        if file_path:
            current_image = Image.new('RGB', (self.grid_width * 20, self.grid_height * 20))
            draw = ImageDraw.Draw(current_image)
            for y, row in enumerate(self.hex_grid):
                for x, color in enumerate(row):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b))
            
            if file_path.endswith('.png'):
                current_image.save(file_path, "PNG")
            elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                quality = simpledialog.askinteger("Quality", "Enter JPEG quality (1-95):", minvalue=1, maxvalue=95, initialvalue=90)
                if quality:
                    current_image.save(file_path, "JPEG", quality=quality)

    def confirm_size(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            if 1 <= width <= 1000 and 1 <= height <= 1000:
                self.grid_width = width
                self.grid_height = height
                self.n_colors = 5  # Default number of colors for clustering
                    
                # Create a blank grid for the first layer
                self.layers = [self.create_blank_grid()]
                self.current_layer = 0
                self.setup_gui()
                self.layer_tree.insert('', 'end', iid=str(self.current_layer), text="Layer 0")
                    
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

    def setup_gui(self):
        self.root.configure(bg='#2B2B2B')
        
        main_frame = Frame(self.root, bg='#2B2B2B')
        main_frame.pack(fill=BOTH, expand=True)

        canvas_frame = Frame(main_frame, bg='white')
        canvas_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        
        max_size = 800
        canvas_width = min(int(self.grid_width * 20 * self.zoom_scale), max_size)
        canvas_height = min(int(self.grid_height * 20 * self.zoom_scale), max_size)
        
        self.canvas = Canvas(canvas_frame, width=canvas_width, height=canvas_height, bg='white', highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=True)
        
        # Define side_panel here
        side_panel = Frame(main_frame, bg='#2B2B2B', width=200)
        side_panel.pack(side=LEFT, fill=Y)

        # Opacity Slider
        opacity_frame = Frame(side_panel, bg='#2B2B2B')
        self.opacity_slider = Scale(opacity_frame, from_=0, to=100, orient=HORIZONTAL, label="Opacity", bg='#2B2B2B', fg='white')
        self.opacity_slider.pack()
        opacity_frame.pack()

        # Now you can call update_image since self.opacity_slider is defined
        self.update_image()
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.on_right_click)
        self.canvas.bind("<B1-Motion>", self.on_draw)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)

        # Rest of the setup_gui code
        self.color_label = Label(side_panel, text="Color Picked: ", fg='white', bg='#2B2B2B')
        self.color_label.pack()

        control_frame = Frame(side_panel, bg='#2B2B2B')
        Button(control_frame, text="Undo", command=self.undo_action, fg='white', bg='#2B2B2B').pack(side="top", fill=X)
        Button(control_frame, text="Redo", command=self.redo_action, fg='white', bg='#2B2B2B').pack(side="top", fill=X)
        control_frame.pack()

        tool_frame = Frame(side_panel, bg='#2B2B2B')
        self.pencil_button = Button(tool_frame, text="✏️", command=lambda: self.set_tool("pencil"), fg='white', bg='#2B2B2B')
        self.pencil_button.pack(fill=X)
        self.erase_button = Button(tool_frame, text="🧹", command=lambda: self.set_tool("erase"), fg='white', bg='#2B2B2B')
        self.erase_button.pack(fill=X)
        tool_frame.pack()

        color_frame = Frame(side_panel, bg='#2B2B2B')
        Button(color_frame, text="Choose Color", command=self.choose_color, fg='white', bg='#2B2B2B').pack(fill=X)
        color_frame.pack()

        # Layer Management with Single-Click Layer Switching
        layer_frame = Frame(side_panel, bg='#2B2B2B')
        Button(layer_frame, text="Add Layer", command=self.add_layer, fg='white', bg='#2B2B2B').pack(fill=X)
        
        self.layer_tree = ttk.Treeview(layer_frame, columns=('Layer Name',), show='tree')
        self.layer_tree.heading('#0', text='Layer Name', anchor='w')
        self.layer_tree.pack(fill=BOTH, expand=True)
        
        # Bind single-click event for layer switching
        self.layer_tree.bind('<Button-1>', self.on_layer_click)
        
        layer_frame.pack()

    def on_layer_click(self, event):
        item = self.layer_tree.identify_row(event.y)
        if item:
            self.current_layer = int(item)
            self.layer_tree.selection_set(item)
            self.update_image()


    def update_image_toggle(self):
        show_all_layers = bool(self.show_all_layers_var.get())
        self.update_image(show_all_layers)

    def update_image(self, show_all_layers=False):
        print(f"Updating Image for Layer: {self.current_layer}")
        if show_all_layers:
            base_img = Image.new('RGBA', (int(self.grid_width * 20), int(self.grid_height * 20)), color=(0, 0, 0, 0))
            for layer_index, layer in enumerate(self.layers):
                opacity = self.opacity_slider.get() if layer_index == self.current_layer else 100
                layer_img = Image.new('RGBA', (int(self.grid_width * 20), int(self.grid_height * 20)))
                draw = ImageDraw.Draw(layer_img)
                
                for y, row in enumerate(layer):
                    for x, color in enumerate(row):
                        r = int(color[1:3], 16)
                        g = int(color[3:5], 16)
                        b = int(color[5:7], 16)
                        alpha = int((opacity / 100.0) * 255)
                        draw.rectangle([x * 20, y * 20, (x + 1) * 20, (y + 1) * 20], fill=(r, g, b, alpha))
                
                base_img = Image.alpha_composite(base_img, layer_img)
        else:
            # Only draw the current layer
            base_img = Image.new('RGBA', (int(self.grid_width * 20), int(self.grid_height * 20)), color=(0, 0, 0, 0))
            current_layer = self.layers[self.current_layer]
            draw = ImageDraw.Draw(base_img)
            for y, row in enumerate(current_layer):
                for x, color in enumerate(row):
                    r = int(color[1:3], 16)
                    g = int(color[3:5], 16)
                    b = int(color[5:7], 16)
                    draw.rectangle([x * 20, y * 20, (x + 1) * 20, (y + 1) * 20], fill=(r, g, b))

        scaled_img = base_img.resize((int(self.grid_width * 20 * self.zoom_scale), int(self.grid_height * 20 * self.zoom_scale)), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(scaled_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)

    def combine_layers(self):
        # Simple layer combining logic
        if len(self.layers) == 1:
            return self.layers[0]
        # Here you would implement logic to combine layers based on their opacity
        # For simplicity, we'll just return the top layer
        return self.layers[self.current_layer]

    def undo_action(self):
        if self.undo_stack:
            self.redo_stack.append(self.layers)
            self.layers = self.undo_stack.pop()
            self.update_image()

    def redo_action(self):
        if self.redo_stack:
            self.undo_stack.append(self.layers)
            self.layers = self.redo_stack.pop()
            self.update_image()

    def add_layer(self):
        new_layer = self.create_blank_grid()
        self.layers.append(new_layer)
        new_layer_index = len(self.layers) - 1
        layer_name = f"Layer {new_layer_index}"
        self.layer_tree.insert('', 'end', iid=str(new_layer_index), text=layer_name)
        self.current_layer = new_layer_index
        self.update_image()

    def start_drag(self, event):
        item = self.layer_tree.identify_row(event.y)
        if item:
            self.dragged_item = item
            self.drag_start_y = event.y


    def dragging(self, event):
        if self.dragged_item:
            delta_y = event.y - self.drag_start_y
            if delta_y < 0:
                prev = self.layer_tree.prev(self.dragged_item)
                if prev:
                    self.layer_tree.move(self.dragged_item, '', self.layer_tree.index(prev))
            elif delta_y > 0:
                next_item = self.layer_tree.next(self.dragged_item)
                if next_item:
                    self.layer_tree.move(self.dragged_item, '', self.layer_tree.index(next_item) + 1)
            self.drag_start_y = event.y


    def stop_drag(self, event):
        if self.dragged_item:
            # Update layers list based on the new order in Treeview
            new_order = list(self.layer_tree.get_children())
            self.layers = [self.layers[self.layer_tree.index(layer)] for layer in new_order]
            self.dragged_item = None
            self.update_image()

    def rename_layer(self, event):
        item = self.layer_tree.selection()[0] if self.layer_tree.selection() else None
        if item:
            current_name = self.layer_tree.item(item, 'text')
            new_name = simpledialog.askstring("Rename Layer", "Enter new name for the layer:", initialvalue=current_name)
            if new_name:
                self.layer_tree.item(item, text=new_name)

    def on_draw(self, event):
        print(f"Drawing on Layer: {self.current_layer}")
        x, y = self.get_grid_coordinates(event)
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            if hasattr(self, 'tool') and self.tool == "pencil" and 0 <= self.current_layer < len(self.layers):
                self.layers[self.current_layer][y][x] = self.draw_color
                self.drawing = True
                self.update_image()
            elif hasattr(self, 'tool') and self.tool == "erase" and 0 <= self.current_layer < len(self.layers):
                self.layers[self.current_layer][y][x] = "#FFFFFF"
                self.drawing = True
                self.update_image()

    def on_click(self, event):
        print(f"Clicking on Layer: {self.current_layer}")
        x, y = self.get_grid_coordinates(event)
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.current_x, self.current_y = x, y
            if hasattr(self, 'tool') and self.tool == "pencil" and 0 <= self.current_layer < len(self.layers):
                self.layers[self.current_layer][y][x] = self.draw_color
                self.update_image()
            elif hasattr(self, 'tool') and self.tool == "erase" and 0 <= self.current_layer < len(self.layers):
                self.layers[self.current_layer][y][x] = "#FFFFFF"  # Assuming white for erase
                self.update_image()
            else:
                if 0 <= self.current_layer < len(self.layers):
                    current_color = self.layers[self.current_layer][y][x]
                    self.open_hex_menu(current_color)

    def get_grid_coordinates(self, event):
        x = int(self.canvas.canvasx(event.x) / (20 * self.zoom_scale))
        y = int(self.canvas.canvasy(event.y) / (20 * self.zoom_scale))
        return x, y

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
                    self.layers[self.current_layer][self.current_y][self.current_x] = new_hex.upper()
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
        for row in self.layers[self.current_layer]:
            formatted_row = '            {' + ', '.join([f'"{color}"' for color in row]) + '},'
            text.insert("end", f"\n{formatted_row}")
        text.insert("end", "\n};")

    def save_changes(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'w') as file:
                json.dump(self.layers[self.current_layer], file)

    def load_changes(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as file:
                self.layers[self.current_layer] = json.load(file)
                self.update_image()

    def import_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        if file_path:
            try:
                # Open a window for color adjustment
                self.color_adjust_window = Toplevel(self.root)  # Set as instance attribute
                self.color_adjust_window.title("Color Adjustment")
                self.color_adjust_window.configure(bg='#2B2B2B')
                self.center_window(self.color_adjust_window)

                Label(self.color_adjust_window, text="Enter number of colors:", fg='white', bg='#2B2B2B').pack(pady=5)
                self.color_count_var = StringVar(value=str(self.n_colors))
                color_count_entry = Entry(self.color_adjust_window, textvariable=self.color_count_var, bg='#404040', fg='white')
                color_count_entry.pack(pady=5)

                # Use lambda to pass self and file_path to confirm_color_count
                Button(self.color_adjust_window, text="Confirm", command=lambda: self.confirm_color_count(file_path), fg='white', bg='#2B2B2B').pack(side="left", padx=5)
                Button(self.color_adjust_window, text="Cancel", command=self.color_adjust_window.destroy, fg='white', bg='#2B2B2B').pack(side="left", padx=5)

            except Exception as e:
                import traceback
                traceback.print_exc()
                messagebox.showerror("Error", f"Failed to import image: {e}")

    def confirm_color_count(self, file_path):
        try:
            color_count = int(self.color_count_var.get())
            if 1 <= color_count <= 256:
                self.n_colors = color_count
                processed_img, new_grid = image_to_grid_print(file_path, self.grid_width, self.grid_height, self.n_colors)
                # Update the current layer
                self.layers[self.current_layer] = new_grid
                self.update_image()
                # Since color_adjust_window is not defined here, we need to make it accessible
                # Assuming it's defined in the import_image method and passed through lambda
                getattr(self, 'color_adjust_window', None).destroy() if hasattr(self, 'color_adjust_window') else None
            else:
                raise ValueError("Color count must be between 1 and 256")
        except ValueError as e:
            messagebox.showerror("Error", str(e))

                
# Example usage
editor = VisualEditor()
editor.run()
