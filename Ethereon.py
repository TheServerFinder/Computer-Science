import asyncio
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import discord
import threading
import time
import re 
import webbrowser
import sys
from datetime import datetime

VERSION = "1.0.9"  # Current client version

TOKEN = 'PRIVATE TOKEN'
CHANNEL_ID = 1333441360639819796
PASSWORD_HANDLING_CHANNEL_ID = 1333512530131423352
UPDATE_CHANNEL_ID = 1333564873984049344  # New channel for version updates
COMMAND_CHANNEL_ID = 1333637833289633802  # Command channel
ROLE_MANAGEMENT_CHANNEL_ID = 1333874464773115967  # Channel ID for storing Tkinter admins
DISCORD_ADMIN_ROLE_ID = 1333240107095949395  # ID for the Discord Admin role

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Global variable to check if update is needed
update_needed = False

class App:
    def __init__(self, master):
        self.master = master
        master.title("Ethereon")
        self.center_window(master, 400, 500)  
        master.configure(bg='#333333')  
        
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        
        master.protocol("WM_DELETE_WINDOW", self.on_closing)
        threading.Thread(target=self.show_login_register).start()

    def center_window(self, window, width, height):
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def show_login_register(self):
        main_window = tk.Toplevel(self.master)
        self.center_window(main_window, 300, 250)
        main_window.title("Login or Register")
        main_window.configure(bg='#333333')
        main_window.transient(self.master)
        main_window.grab_set()

        tk.Label(main_window, text="Username:", bg='#333333', fg='white').pack(pady=5)
        username_entry = tk.Entry(main_window, width=30, textvariable=self.username)
        username_entry.pack(pady=5)

        tk.Label(main_window, text="Password:", bg='#333333', fg='white').pack(pady=5)
        password_entry = tk.Entry(main_window, width=30, show='*', textvariable=self.password)
        password_entry.pack(pady=5)

        tk.Label(main_window, text="Confirm Password:", bg='#333333', fg='white').pack(pady=5)
        confirm_password_entry = tk.Entry(main_window, width=30, show='*', textvariable=self.confirm_password)
        confirm_password_entry.pack(pady=5)

        warning_label = tk.Label(main_window, text="Warning: Do not use a password\n you use for anything else!", bg='#333333', fg='brown')
        warning_label.pack(pady=5)

        tk.Button(main_window, text="Login", command=lambda: self.login_or_register("login"), bg='#444444', fg='white').pack(pady=5, side=tk.LEFT, padx=20)
        tk.Button(main_window, text="Register", command=lambda: self.login_or_register("register"), bg='#444444', fg='white').pack(pady=5, side=tk.RIGHT, padx=20)

        main_window.wait_window()

    def login_or_register(self, action):
        username = self.username.get().lower()  # Consistent case conversion
        password = self.password.get()
        confirm = self.confirm_password.get()
        
        main_window = self.master.winfo_children()[0] if self.master.winfo_children() else None
        
        # Check if username length is between 1 and 30 characters
        if not (1 <= len(username) <= 30):
            messagebox.showerror("Error", "Username must be between 1 and 30 characters long.")
            return

        if not re.match(r'^[a-zA-Z0-9]+$', username):
            messagebox.showerror("Error", "Username can only contain letters and numbers.")
            return

        if action == "login":
            if password == confirm:
                if asyncio.run_coroutine_threadsafe(self.verify_login(username, password), client.loop).result():
                    if main_window:
                        main_window.destroy()
                    self.setup_main_interface() 
                    self.start_chat_session()
                else:
                    messagebox.showerror("Error", "Invalid username or password.")
            else:
                messagebox.showerror("Error", "Passwords do not match.")
        else:  # Register
            if password == confirm:
                if 4 <= len(password) <= 16:
                    if asyncio.run_coroutine_threadsafe(self.register_user(username, password), client.loop).result():
                        if main_window:
                            main_window.destroy()
                        self.setup_main_interface()
                        self.start_chat_session()
                    else:
                        messagebox.showerror("Error", "Registration failed, username might already be taken.")
                else:
                    messagebox.showerror("Error", "Password must be between 4 and 16 characters long.")
            else:
                messagebox.showerror("Error", "Passwords do not match.")

    async def register_user(self, username, password):
        password_channel = client.get_channel(PASSWORD_HANDLING_CHANNEL_ID)
        if password_channel:
            try:
                await password_channel.send(f"{username.lower()}:{password}")
                return True
            except Exception as e:
                print(f"Failed to register user: {e}")
        return False

    async def verify_login(self, username, password):
        password_channel = client.get_channel(PASSWORD_HANDLING_CHANNEL_ID)
        if password_channel:
            async for message in password_channel.history(limit=None):
                stored_user_pass = message.content.split(':')
                if stored_user_pass[0].lower() == username and stored_user_pass[1] == password:
                    return True
        return False

    def setup_main_interface(self):
        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=45, height=25, bg='#444444', fg='white', padx=5, pady=5)
        self.chat_area.pack(expand=True, fill=tk.BOTH)  
        self.chat_area.config(state=tk.DISABLED)
        
        # Tag configurations
        self.chat_area.tag_config('my_message', background='#1E90FF', foreground='white', relief=tk.FLAT, borderwidth=0, spacing1=2, spacing3=2)
        self.chat_area.tag_config('separator', background='#444444', foreground='#444444')
        self.chat_area.tag_config('other_message', background='#D3D3D3', foreground='black', relief=tk.FLAT, borderwidth=0, spacing1=2, spacing3=2)
        self.chat_area.tag_config('alert', background='yellow', foreground='black')
        self.chat_area.tag_config('link', foreground="blue", underline=True)

        # New tag for system messages
        self.chat_area.tag_config('system', background='#555555', foreground='white')

        self.message_entry = tk.Entry(self.master, width=45, bg='#444444', fg='white')
        self.message_entry.pack(expand=True, fill=tk.X, padx=5, pady=5)
        self.message_entry.bind('<Return>', lambda event: self.send_message())

        send_button = tk.Button(self.master, text="Send", command=self.send_message, bg='#555555', fg='white')
        send_button.pack(expand=True, pady=5)

    def send_system_message(self, message):
        if hasattr(self, 'chat_area'):
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, f"{message}\n", 'system')
            self.chat_area.insert(tk.END, "-\n", 'separator')
            self.chat_area.config(state=tk.DISABLED)
            self.chat_area.see(tk.END)

    def send_message(self):
        if self.username.get():
            message = self.message_entry.get()
            if message:
                if len(message) > 750:
                    messagebox.showerror("Error", "Message exceeds the 750 character limit.")
                    return
                
                if message.startswith('!'):  # Check if it's a command
                    asyncio.run_coroutine_threadsafe(self.execute_command(message), client.loop)
                else:
                    asyncio.run_coroutine_threadsafe(self.send_to_discord(message), client.loop)
                self.message_entry.delete(0, tk.END)

    def start_chat_session(self):
        asyncio.run_coroutine_threadsafe(self.send_system_event("join"), client.loop)

    def user_left(self):
        print("User left method called")
        asyncio.run_coroutine_threadsafe(self.send_system_event("leave"), client.loop)
        print("System leave event sent")

    async def send_system_event(self, event_type):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            try:
                if event_type == "join":
                    await channel.send(f"[SYSTEM] {self.username.get()} has joined the chat.")
                elif event_type == "leave":
                    await channel.send(f"[SYSTEM] {self.username.get()} has left the chat.")
            except discord.errors.HTTPException as e:
                print(f"Failed to send system event: {e}")

    async def send_to_discord(self, message):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            try:
                print(f"Attempting to send: [RELAY] {self.username.get()}: {message}")
                await channel.send(f"[RELAY] {self.username.get()}: {message}")
                print("Message sent successfully")
            except discord.errors.HTTPException as e:
                print(f"Failed to send message: {e}")
        else:
            print("Channel not found")

    async def check_update_status(self):
        update_channel = client.get_channel(UPDATE_CHANNEL_ID)
        if update_channel:
            async for message in update_channel.history(limit=1):
                try:
                    latest_version, download_link = message.content.split()
                    # Convert versions to tuple for comparison if they are in 'x.y.z' format
                    current_version_tuple = tuple(map(int, VERSION.split('.')))
                    latest_version_tuple = tuple(map(int, latest_version.split('.')))
                    
                    if current_version_tuple < latest_version_tuple:
                        result = messagebox.showinfo("Update Required", 
                                                    f"An update is available ({latest_version}). The application will now close.",
                                                    detail="Click OK to update and close the application.")
                        if result == 'ok':  # This condition will always be true for showinfo, but it's here for clarity
                            webbrowser.open(download_link)
                            self.master.quit()  # Force quit the application
                except ValueError:
                    # Handle the case where the message content might not be in the expected format
                    print(f"Error parsing update message: {message.content}")
        else:
            print("Update channel not found.")

    def on_closing(self):
        global update_needed  # Declare update_needed as global
        if self.username.get():
            self.user_left()
        if update_needed:
            update_needed = False  # Reset on closing if update was triggered
        self.master.quit()

    async def execute_command(self, command):
        user = self.username.get().lower()
        if await self.is_user_admin(user):
            parts = command.split(' ', 1)
            if len(parts) > 1:
                cmd, args = parts[0], parts[1]
                if cmd == '!admin':
                    if await self.is_user_admin(args.lower()):
                        self.send_system_message(f"{args} is already an admin.")
                    else:
                        await self.add_admin(args.lower())
                        self.send_system_message(f"Set {args} to admin.")
                elif cmd == '!removeadmin':
                    if await self.is_user_admin(args.lower()):
                        await self.remove_admin(args.lower())
                        self.send_system_message(f"Removed {args} from admin.")
                    else:
                        self.send_system_message(f"{args} is not an admin.")
                elif cmd == '!help':
                    self.send_system_message("**Available commands:**\n- `!help`: Lists all available commands.\n- `!update`: Forces all clients to check for updates.\n- `!admin <username>`: Adds user to admin list.\n- `!removeadmin <username>`: Removes user from admin list.")
                else:
                    # For any other commands, you might want to implement specific handling here
                    self.send_system_message(f"Unknown command: {cmd}")
            else:
                if command == '!help':
                    self.send_system_message("**Available commands:**\n- `!help`: Lists all available commands.\n- `!update`: Forces all clients to check for updates.\n- `!admin <username>`: Adds user to admin list.\n- `!removeadmin <username>`: Removes user from admin list.")
                else:
                    self.send_system_message(f"Command '{command}' requires an argument.")
        else:
            self.send_system_message(f"You do not have permission to execute commands.")

    async def is_user_admin(self, username):
        role_channel = client.get_channel(ROLE_MANAGEMENT_CHANNEL_ID)
        if role_channel:
            async for message in role_channel.history(limit=None):
                if message.content.lower() == username:
                    return True
        return False

    async def add_admin(self, username):
        role_channel = client.get_channel(ROLE_MANAGEMENT_CHANNEL_ID)
        if role_channel:
            await role_channel.send(username)

    async def remove_admin(self, username):
        role_channel = client.get_channel(ROLE_MANAGEMENT_CHANNEL_ID)
        if role_channel:
            async for msg in role_channel.history(limit=None):
                if msg.content.lower() == username:
                    await msg.delete()
                    return

async def check_version():
    global update_needed
    update_channel = client.get_channel(UPDATE_CHANNEL_ID)
    if update_channel:
        async for message in update_channel.history(limit=1):
            try:
                latest_version, download_link = message.content.split()
                current_version_tuple = tuple(map(int, VERSION.split('.')))
                latest_version_tuple = tuple(map(int, latest_version.split('.')))
                
                if current_version_tuple < latest_version_tuple:
                    update_needed = True
                    result = messagebox.showinfo("Update Required", 
                                                f"An update is available ({latest_version}). The application will now close.",
                                                detail="Click OK to update and close the application.")
                    if result == 'ok':  # This condition will always be true for showinfo, but it's here for clarity
                        webbrowser.open(download_link)
                        app.master.quit()  # Force quit the application
            except ValueError:
                print(f"Error parsing update message: {message.content}")
    else:
        print("Update channel not found.")

@client.event
async def on_ready():
    await check_version()  # Check for updates once at startup
    if hasattr(app, 'chat_area'):  
        app.chat_area.config(state=tk.NORMAL)
        app.chat_area.insert(tk.END, f"Successfully connected to Etheron API.\n", 'system')
        app.chat_area.config(state=tk.DISABLED)
        app.chat_area.see(tk.END)
        print("Bot is ready and connected!")

@client.event
async def on_disconnect():
    print("Client disconnected.")

@client.event
async def on_message(message):
    if message.channel.id == COMMAND_CHANNEL_ID and not message.author.bot:
        content = message.content.lower()
        if content.startswith('!help'):
            await message.channel.send("**Available commands:**\n- `!help`: Lists all available commands.\n- `!update`: Forces all clients to check for updates.\n- `!admin <username>`: Adds user to admin list.\n- `!removeadmin <username>`: Removes user from admin list.")
        elif content.startswith('!update'):
            await message.channel.send("All clients will now check for updates.")
            asyncio.run_coroutine_threadsafe(update_all_clients(), client.loop)
        elif any(role.id == DISCORD_ADMIN_ROLE_ID for role in message.author.roles):  # Check if user has Discord Admin role
            parts = content.split(' ', 1)
            if len(parts) > 1:
                cmd, args = parts[0], parts[1]
                if cmd == '!admin':
                    if await app.is_user_admin(args.lower()):
                        await message.channel.send(f"{args} is already an admin.")
                    else:
                        await app.add_admin(args.lower())
                        await message.channel.send(f"Set {args} to admin.")
                elif cmd == '!removeadmin':
                    if await app.is_user_admin(args.lower()):
                        await app.remove_admin(args.lower())
                        await message.channel.send(f"Removed {args} from admin.")
                    else:
                        await message.channel.send(f"{args} is not an admin.")
                else:
                    # For any other commands, you might want to implement specific handling here
                    await message.channel.send(f"Unknown command: {cmd}")
            else:
                await message.channel.send("Command requires an argument.")
        return  # Return to avoid processing these as regular messages
    
    if message.author == client.user:
        if message.content.startswith("[SYSTEM]"):
            if hasattr(app, 'chat_area'):
                try:
                    app.chat_area.config(state=tk.NORMAL)
                    system_message = message.content.split('[SYSTEM] ', 1)[1]
                    app.chat_area.insert(tk.END, f"{system_message}\n", 'system')
                    app.chat_area.insert(tk.END, "-\n", 'separator')
                    app.chat_area.config(state=tk.DISABLED)
                    app.chat_area.see(tk.END)
                except Exception as e:
                    print(f"Error updating chat area with system message: {e}")
                    app.chat_area.config(state=tk.DISABLED)
            return
        if not message.content.startswith("[RELAY]"):
            return 
    
    if message.channel.id == CHANNEL_ID:
        content = message.content
        if content.startswith("[RELAY] "):
            name, content = content[8:].split(': ', 1) 
            if hasattr(app, 'chat_area'):
                try:
                    app.chat_area.config(state=tk.NORMAL)
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    # Ensure the entire line is tagged
                    if name != app.username.get():
                        tag = 'other_message'
                    else:
                        tag = 'my_message'
                    
                    full_message = f"[{timestamp}] {name}: {content}\n"
                    app.chat_area.insert(tk.END, full_message, tag)

                    # Apply link formatting
                    start_index = app.chat_area.index(tk.END + "-1l linestart")
                    for m in re.finditer(r'https?://\S+', content):
                        app.chat_area.tag_add('link', f"{start_index}+{len(f'[{timestamp}] {name}: ')+m.start()}c", 
                                              f"{start_index}+{len(f'[{timestamp}] {name}: ')+m.end()}c")
                        app.chat_area.tag_bind('link', '<Button-1>', lambda e, url=m.group(0): webbrowser.open(url))
                    
                    # Insert a separator
                    app.chat_area.insert(tk.END, "-\n", 'separator')
                    app.chat_area.config(state=tk.DISABLED)
                    app.chat_area.see(tk.END)
                    print(f"Message from {name}: {content} has been displayed")
                except Exception as e:
                    print(f"Error updating chat area: {e}")
                    app.chat_area.config(state=tk.DISABLED)

async def update_all_clients():
    global update_needed
    update_needed = False  # Reset before checking
    await check_version()  # Check for updates manually

def run_discord_client():
    def run():
        asyncio.run(client.start(TOKEN))
        try:
            while True:
                asyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            pass

    thread = threading.Thread(target=run, daemon=True)
    thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)  
    run_discord_client()
    root.mainloop()
