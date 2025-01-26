from PIL import Image, ImageDraw, ImageTk
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
from tkinter import Tk, Label, Button, Canvas, colorchooser, simpledialog, messagebox, filedialog, Toplevel, Text, Scrollbar, StringVar, Entry, Frame
import json

class VisualEditor:
    def __init__(self):
        self.root = Tk()
        self.root.title("Clarks Advanced Pixel Editor")
        # Withdraw the main window initially
        self.root.withdraw()
        self.setup_initial_ui()

    def setup_initial_ui(self):
        # Create a single dialog window for both width and height
        self.size_window = Toplevel(self.root)
        self.size_window.title("Grid Size")
        # Center the size_window
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
        # Wait for the size window to be closed before proceeding
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
                
                # New attributes for drawing tools
                self.draw_color = "#000000"  # Default color for drawing
                self.drawing = False
                self.tool = None  # Initialize tool to None
                # Show the main window after confirmation
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
        # Set the background of the UI to dark gray and text to white
        self.root.configure(bg='#2B2B2B')
        
        # Create a frame for the black border
        border_frame = Frame(self.root, bg='#2B2B2B', padx=40, pady=40)  # Adjust padx and pady for border width
        border_frame.pack(fill='both', expand=True)
        
        # Create a white frame inside the black border
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
        
        # Additional controls
        control_frame = Frame(self.root, bg='#2B2B2B')
        Button(control_frame, text="Print Hex Grid", command=self.print_hex_grid, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Save Changes", command=self.save_changes, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Load Changes", command=self.load_changes, fg='white', bg='#2B2B2B').pack(side="left")
        Button(control_frame, text="Import Image", command=self.import_image, fg='white', bg='#2B2B2B').pack(side="left")
        control_frame.pack()
        
        # Tool selection
        tool_frame = Frame(self.root, bg='#2B2B2B')
        self.pencil_button = Button(tool_frame, text="Pencil", command=lambda: self.set_tool("pencil"), fg='white', bg='#2B2B2B')
        self.pencil_button.pack(side="left")
        self.erase_button = Button(tool_frame, text="Erase", command=lambda: self.set_tool("erase"), fg='white', bg='#2B2B2B')
        self.erase_button.pack(side="left")
        tool_frame.pack()
        
        # Color selection
        color_frame = Frame(self.root, bg='#2B2B2B')
        Button(color_frame, text="Choose Color", command=self.choose_color, fg='white', bg='#2B2B2B').pack(side="left")
        color_frame.pack()

    def update_image(self):
        # Create a new image based on the grid
        new_img = Image.new('RGB', (self.grid_width * 20, self.grid_height * 20), color='white')  # Ensure white background
        draw = ImageDraw.Draw(new_img)
        
        for y, row in enumerate(self.hex_grid):
            for x, color in enumerate(row):
                r = int(color[1:3], 16)
                g = int(color[3:5], 16)
                b = int(color[5:7], 16)
                draw.rectangle([x*20, y*20, (x+1)*20, (y+1)*20], fill=(r, g, b), outline=(r, g, b))  # Set outline to match fill
        
        # Convert to PhotoImage for Tkinter
        self.photo = ImageTk.PhotoImage(new_img)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
        
        # Draw hex grid on top
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
                # Load the image
                img = Image.open(file_path).convert('RGB')
                # Calculate segment sizes
                self.segment_width = img.width // self.grid_width
                self.segment_height = img.height // self.grid_height
                # Create the hex grid using the original logic
                self.hex_grid = self.create_hex_grid_from_image(img)
                # Update the canvas to reflect the new grid
                self.update_image()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to import image: {e}")

    def create_hex_grid_from_image(self, img):
        color_rows = []
        for i in range(self.grid_height):
            row_colors = []
            for j in range(self.grid_width):
                left, top = j * self.segment_width, i * self.segment_height
                right = min(left + self.segment_width, img.width)
                bottom = min(top + self.segment_height, img.height)
                
                block = img.crop((left, top, right, bottom))
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

    def center_window(self, window):
        # Get the screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Get the window width and height
        window_width = window.winfo_reqwidth()
        window_height = window.winfo_reqheight()
        
        # Calculate position for centering
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # Set the window's position
        window.geometry(f"+{x}+{y}")

    def run(self):
        self.root.mainloop()

# Example usage
editor = VisualEditor()
editor.run()
