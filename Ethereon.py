import tkinter as tk
from tkinter import scrolledtext, simpledialog
import discord
from discord.ext import commands
import asyncio
import threading

TOKEN = 'HIDDEN'
CHANNEL_ID = 1333441360639819796

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

class App:
    def __init__(self, master):
        self.master = master
        master.title("Discord Chat Client")
        
        self.username = simpledialog.askstring("Username", "Enter your username:", parent=master) or "Anonymous"
        
        self.message_entry = tk.Entry(master, width=50)
        self.message_entry.pack()

        self.send_button = tk.Button(master, text="Send", command=self.send_message)
        self.send_button.pack()

        self.chat_area = scrolledtext.ScrolledText(master, wrap=tk.WORD, width=50, height=10)
        self.chat_area.pack()

    def send_message(self):
        message = self.message_entry.get()
        if message:
            asyncio.run_coroutine_threadsafe(self.send_to_discord(message), client.loop)
            self.message_entry.delete(0, tk.END)  # Clear the entry field after sending

    async def send_to_discord(self, message):
        channel = client.get_channel(CHANNEL_ID)
        if channel:
            # Add a special identifier to prevent looping
            await channel.send(f"[RELAY] {self.username}: {message}")

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    app.chat_area.insert(tk.END, f"{client.user} has connected to Discord!\n")
    app.chat_area.see(tk.END)

@client.event
async def on_message(message):
    if message.author == client.user:
        # Check if the message is a relay message to avoid looping
        if not message.content.startswith("[RELAY]"):
            return  # Ignore messages from this bot that are not intended for relaying
    
    if message.channel.id == CHANNEL_ID:
        content = message.content
        if content.startswith("[RELAY] "):
            content = content[8:]  # Remove the "[RELAY] " prefix
        
        # Parse message to separate username and content
        if ": " in content:
            name, text = content.split(": ", 1)
            app.chat_area.insert(tk.END, f"{name}: {text}\n")
        else:
            app.chat_area.insert(tk.END, f"{message.author}: {content}\n")
        app.chat_area.see(tk.END)
        
        # Relay the message back to all clients including this one via the bot
        if not message.content.startswith("[RELAY]"):  # Only relay if it's not already a relay message
            await message.channel.send(f"[RELAY] {message.content}")

def run_discord_client():
    def run():
        asyncio.run(client.start(TOKEN))

    thread = threading.Thread(target=run)
    thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)  # Here, 'app' is defined for use in event handlers
    run_discord_client()
    root.mainloop()