import asyncio
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import discord
import threading
import time
import re 

TOKEN = ''
CHANNEL_ID = 1333441360639819796
DATACHANNEL_ID = 1333455271477117029  
PASSWORD_HANDLING_CHANNEL_ID = 1333512530131423352

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

class App:
    def __init__(self, master):
        self.master = master
        master.title("Ethereon")
        self.center_window(master, 400, 500)  
        master.configure(bg='#333333')  
        
        self.username = tk.StringVar()
        self.password = tk.StringVar()
        self.confirm_password = tk.StringVar()
        threading.Thread(target=self.show_login_register).start()
        
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

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

        warning_label = tk.Label(main_window, text="Warning: Do not use a password you use for anything else!", bg='#333333', fg='red')
        warning_label.pack(pady=5)

        # Buttons should be here, in the method where main_window is defined
        tk.Button(main_window, text="Login", command=lambda: self.login_or_register("login"), bg='#444444', fg='white').pack(pady=5, side=tk.LEFT, padx=20)
        tk.Button(main_window, text="Register", command=lambda: self.login_or_register("register"), bg='#444444', fg='white').pack(pady=5, side=tk.RIGHT, padx=20)

        main_window.wait_window()


    def login_or_register(self, action):
        username = self.username.get().lower()  # Consistent case conversion
        password = self.password.get()
        confirm = self.confirm_password.get()
        
        # Use the actual login window, not self.master
        main_window = self.master.winfo_children()[0] if self.master.winfo_children() else None
        
        # Check if username only contains letters and numbers
        if not re.match(r'^[a-zA-Z0-9]+$', username):
            messagebox.showerror("Error", "Username can only contain letters and numbers.")
            return

        if action == "login":
            if password == confirm:
                if asyncio.run_coroutine_threadsafe(self.verify_login(username, password), client.loop).result():
                    # Destroy the login window, not the master
                    if main_window:
                        main_window.destroy()
                    self.setup_main_interface()  # Now this will add to self.master
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
        data_channel = client.get_channel(DATACHANNEL_ID)
        password_channel = client.get_channel(PASSWORD_HANDLING_CHANNEL_ID)
        if data_channel and password_channel:
            try:
                # Check if username exists
                async for message in data_channel.history(limit=None):
                    if message.content.lower() == username.lower():
                        return False  # Username already exists

                # If username is unique, proceed with registration
                await data_channel.send(username.lower())  # Store in lowercase
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
                if stored_user_pass[0].lower() == username and stored_user_pass[1] == password:  # Case-insensitive username check
                    return True
        return False

    def setup_main_interface(self):
        # Chat area
        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=45, height=25, bg='#444444', fg='white')
        self.chat_area.pack(expand=True)  
        self.chat_area.config(state=tk.DISABLED)  # Disable direct editing of chat area
        self.chat_area.tag_config('my_message', foreground='yellow')  # Configure tag for user's messages

        # Message entry
        self.message_entry = tk.Entry(self.master, width=45, bg='#444444', fg='white')
        self.message_entry.pack(expand=True)
        self.message_entry.bind('<Return>', lambda event: self.send_message())  # Bind enter key to send

        # Send button
        send_button = tk.Button(self.master, text="Send", command=self.send_message, bg='#555555', fg='white')
        send_button.pack(expand=True, pady=5)

    def send_message(self):
        if self.username.get():
            message = self.message_entry.get()
            if message:
                asyncio.run_coroutine_threadsafe(self.send_to_discord(message), client.loop)
                self.message_entry.delete(0, tk.END)

    def start_chat_session(self):
        threading.Thread(target=self.delay_send_connection_message).start()

    def delay_send_connection_message(self):
        while not client.is_ready() or not self.username.get():
            time.sleep(1)
        asyncio.run_coroutine_threadsafe(self.send_connection_message(), client.loop)
        print("Connection message delay thread completed.")

    async def send_connection_message(self):
        await self.send_to_discord("connection success!")

    async def send_to_discord(self, message):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            try:
                # Send username as entered by user to Discord
                await channel.send(f"[RELAY] {self.username.get()}: {message}")
                print(f"Message sent to discord: [RELAY] {self.username.get()}: {message}")
            except discord.errors.HTTPException as e:
                print(f"Failed to send message: {e}")

    def on_closing(self):
        if self.username.get():
            print("Application is exiting, attempting to clean up...")
            try:
                loop = client.loop
                if loop.is_running():
                    # If the loop is already running, schedule the coroutine safely
                    cleanup_future = asyncio.run_coroutine_threadsafe(self.remove_user_from_list(self.username.get().lower()), loop)
                    cleanup_future.result(timeout=10)  # Wait for up to 10 seconds
                else:
                    # If the loop is not running, we can run it directly
                    loop.run_until_complete(asyncio.wait_for(self.remove_user_from_list(self.username.get().lower()), timeout=10))
                print("Cleanup completed successfully.")
            except asyncio.TimeoutError:
                print("Cleanup operation timed out.")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        self.master.quit()

    async def remove_user_from_list(self, username):
        data_channel = client.get_channel(DATACHANNEL_ID)
        if data_channel:
            async for message in data_channel.history(limit=100):
                if message.content.lower() == username:  # Case-insensitive username check
                    try:
                        await message.delete()
                        print(f"Successfully deleted username: {username}")
                        return True
                    except Exception as e:
                        print(f"Error deleting message for {username}: {e}")
            print(f"Username {username} not found in the channel to remove.")
            return True  
        return False

@client.event
async def on_disconnect():
    if hasattr(app, 'username') and app.username.get():
        print("Attempting to remove user from data channel due to disconnection...")
        try:
            await app.remove_user_from_list(app.username.get())
            print(f"User {app.username.get()} has been removed from the data channel due to disconnection.")
        except Exception as e:
            print(f"Error removing user from data channel on disconnect: {e}")

@client.event
async def on_ready():
    if hasattr(app, 'chat_area'):  # Ensure chat_area exists
        app.chat_area.config(state=tk.NORMAL)
        app.chat_area.insert(tk.END, f"Successfully connected to Etheron API.\n")
        app.chat_area.config(state=tk.DISABLED)
        app.chat_area.see(tk.END)
        print("Bot is ready and online.")

@client.event
async def on_message(message):
    if message.author == client.user:
        if not message.content.startswith("[RELAY]"):
            return  # Ignore messages from this bot that are not intended for relaying
    
    if message.channel.id == CHANNEL_ID:
        content = message.content
        if content.startswith("[RELAY] "):
            name, content = content[8:].split(': ', 1)  # Correctly parse the name and message
            if hasattr(app, 'chat_area'):
                app.chat_area.config(state=tk.NORMAL)
                if name == app.username.get():
                    app.chat_area.insert(tk.END, f"{name} (you): {content}\n", 'my_message')
                else:
                    app.chat_area.insert(tk.END, f"{name}: {content}\n")
                app.chat_area.config(state=tk.DISABLED)
                app.chat_area.see(tk.END)

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
    app = App(root)  # Here, 'app' is defined for use in event handlers
    run_discord_client()
    root.mainloop()
