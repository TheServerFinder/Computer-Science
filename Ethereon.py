import asyncio
import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import discord
import threading
import time
import asyncio


TOKEN = ''
CHANNEL_ID = 1333441360639819796
DATACHANNEL_ID = 1333455271477117029  # Example ID for the data channel

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

class App:
    def __init__(self, master):
        self.master = master
        master.title("Ethereon")
        self.center_window(master, 400, 500)  # Center the window on the screen
        master.configure(bg='#333333')  # Dark gray background
        
        self.username = tk.StringVar()
        threading.Thread(target=self.get_username_async).start()
        self.setup_main_interface()
        threading.Thread(target=self.delay_send_connection_message).start()
        
        # Bind the close event to our own method
        master.protocol("WM_DELETE_WINDOW", self.on_closing)

    def center_window(self, window, width, height):
        # Get screen width and height
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate position for centering
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")

    def get_username_async(self):
        while not self.username.get():
            username = self.get_username()
            if username:
                self.username.set(username)
                asyncio.run_coroutine_threadsafe(self.check_username_uniqueness(), client.loop)
                print(f"Username set to {username}")

    def get_username(self):
        while True:
            username_window = tk.Toplevel(self.master)
            self.center_window(username_window, 300, 100)
            username_window.title("Set Username")
            username_window.configure(bg='#333333')
            username_window.transient(self.master)
            username_window.grab_set()

            tk.Label(username_window, text="Enter your username:", bg='#333333', fg='white').pack(pady=5)
            username_entry = tk.Entry(username_window, width=30)
            username_entry.pack(pady=5)
            username_entry.focus_set()

            result = tk.StringVar()
            def confirm_username():
                entered_name = username_entry.get()
                if not entered_name:
                    entered_name = "Anonymous0"
                result.set(entered_name)
                username_window.destroy()

            tk.Button(username_window, text="Confirm", command=confirm_username, bg='#444444', fg='white').pack(pady=5)
            username_window.wait_window()  # Wait for the window to be closed
            
            return result.get()

    async def check_username_uniqueness(self):
        base_name = self.username.get()
        if base_name.lower().startswith("anonymous") and base_name != "Anonymous":
            counter = 1
            while not await self.is_username_unique(base_name):
                base_name = f"Anonymous{counter}"
                counter += 1
            self.username.set(base_name)
            self.chat_area.config(state=tk.NORMAL)
        elif base_name == "Anonymous" and not await self.is_username_unique("Anonymous"):
            counter = 1
            while not await self.is_username_unique(f"Anonymous{counter}"):
                counter += 1
            base_name = f"Anonymous{counter}"
            self.username.set(base_name)
            self.chat_area.config(state=tk.NORMAL)
        elif not await self.is_username_unique(base_name):
            self.username.set("")
            messagebox.showerror("Error", "Username already taken. Please choose another.")
            self.master.after(1, self.get_username_async)  # Schedule the username selection again
        else:
            self.chat_area.config(state=tk.NORMAL)
            self.chat_area.insert(tk.END, f"Username {base_name} is unique.\n")

        self.chat_area.config(state=tk.DISABLED)
        self.chat_area.see(tk.END)
        self.message_entry.config(state=tk.NORMAL)

    async def is_username_unique(self, username):
        try:
            user_list = await self.fetch_user_list()
            return username not in user_list
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check username availability: {str(e)}")
            return True  # If we can't check, assume it's unique to avoid lockout

    async def fetch_user_list(self):
        for attempt in range(5):
            try:
                data_channel = client.get_channel(DATACHANNEL_ID)
                if data_channel:
                    user_list = []
                    async for message in data_channel.history(limit=None):
                        user_list.append(message.content)
                    print(f"Fetched {len(user_list)} usernames from data channel.")
                    return user_list
                else:
                    await asyncio.sleep(1 + attempt)  # Wait longer with each attempt
            except AttributeError:
                await asyncio.sleep(1 + attempt)  # Wait longer with each attempt
        messagebox.showerror("Error", "Data channel not found after multiple attempts.")
        return []

    def setup_main_interface(self):
        # Chat area
        self.chat_area = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=45, height=25, bg='#444444', fg='white')
        self.chat_area.pack(expand=True)  
        self.chat_area.config(state=tk.DISABLED)  # Disable direct editing of chat area
        self.chat_area.tag_config('my_message', foreground='yellow')  # Configure tag for user's messages

        # Message entry
        self.message_entry = tk.Entry(self.master, width=45, bg='#444444', fg='white', state=tk.DISABLED)  # Start disabled
        self.message_entry.pack(expand=True)
        self.message_entry.bind('<Return>', lambda event: self.send_message())  # Bind enter key to send

        # Send button
        send_button = tk.Button(self.master, text="Send", command=self.send_message, bg='#555555', fg='white')
        send_button.pack(expand=True, pady=5)
        
    def send_message(self):
        if self.username.get() and self.message_entry['state'] == tk.NORMAL:
            message = self.message_entry.get()
            if message:
                asyncio.run_coroutine_threadsafe(self.send_to_discord(message), client.loop)
                self.message_entry.delete(0, tk.END)
                self.chat_area.config(state=tk.NORMAL)
                self.chat_area.config(state=tk.DISABLED)
                self.chat_area.see(tk.END)
        else:
            messagebox.showerror("Error", "Please set a unique username to chat.")

    def delay_send_connection_message(self):
        while not client.is_ready() or not self.username.get():
            time.sleep(1)
        asyncio.run_coroutine_threadsafe(self.add_user_to_list(self.username.get()), client.loop)
        asyncio.run_coroutine_threadsafe(self.send_connection_message(), client.loop)
        print("Connection message delay thread completed.")

    async def add_user_to_list(self, username):
        data_channel = client.get_channel(DATACHANNEL_ID)
        if data_channel:
            print(f"Attempting to add username {username}")
            # Clear any previous username messages before adding a new one
            async for message in data_channel.history(limit=100):  # Reduced limit for performance
                if message.content == username:
                    try:
                        await message.delete()
                        print(f"Deleted existing message for {username}")
                    except Exception as e:
                        print(f"Failed to delete existing message for {username}: {e}")
            try:
                await data_channel.send(username)
                print(f"Added {username} to the data channel.")
                return True
            except Exception as e:
                print(f"Failed to send message for {username}: {e}")
                return False
        return False

    async def remove_user_from_list(self, username):
        data_channel = client.get_channel(DATACHANNEL_ID)
        print(f"Starting Removal")
        if data_channel:
            print(f"Found Channel")
            async for message in data_channel.history(limit=100):
                if message.content == username:
                    print(f"Found Username")
                    try:
                        await message.delete()
                        print(f"Successfully deleted username: {username}")
                        return True
                    except Exception as e:
                        print(f"Error deleting message for {username}: {e}")
            print(f"Username {username} not found in the channel to remove.")
            return True  # Consider successful if username wasn't found to delete
        return False

    async def send_connection_message(self):
        await self.send_to_discord("connection success!")

    async def send_to_discord(self, message):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            try:
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
                    cleanup_future = asyncio.run_coroutine_threadsafe(self.remove_user_from_list(self.username.get()), loop)
                    # Wait for the future to complete with a timeout to not block indefinitely
                    cleanup_future.result(timeout=10)  # Wait for up to 10 seconds
                else:
                    # If the loop is not running, we can run it directly
                    loop.run_until_complete(asyncio.wait_for(self.remove_user_from_list(self.username.get()), timeout=10))
                print("Cleanup completed successfully.")
            except asyncio.TimeoutError:
                print("Cleanup operation timed out.")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        self.master.quit()

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
        # More robust check for data channel
        for attempt in range(5):
            data_channel = client.get_channel(DATACHANNEL_ID)
            if data_channel:
                app.chat_area.config(state=tk.NORMAL)
                app.chat_area.insert(tk.END, "Data channel successfully found.\n")
                app.chat_area.config(state=tk.DISABLED)
                app.chat_area.see(tk.END)
                break
            else:
                await asyncio.sleep(1)
        else:
            app.chat_area.config(state=tk.NORMAL)
            app.chat_area.insert(tk.END, "Warning: Data channel not found after multiple attempts.\n")
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
        # Keep the loop running even after client.start() returns
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
