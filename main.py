import customtkinter as ctk
from tkinter import filedialog
import requests
import json
import os

# Load or create config.json
CONFIG_FILE = 'config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {'github_token': ''}

# Function to mask the token
def mask_token(token):
    if len(token) <= 10:
        return '*' * len(token)
    return token[:4] + '*' * (len(token) - 8) + token[-4:]

# Tooltip function
class Tooltip(ctk.CTkToplevel):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.wm_overrideredirect(True)
        self.wm_geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() + 20}")
        label = ctk.CTkLabel(self, text=text, justify="left", wraplength=200)
        label.pack(ipadx=5, ipady=5)

# Custom Messagebox using CTkToplevel
class CTkMessagebox(ctk.CTkToplevel):
    def __init__(self, title="Message", message="This is a message"):
        super().__init__()

        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        self.grab_set()  # Set the focus on this window

        ctk.CTkLabel(self, text=message, wraplength=250, justify="center").pack(pady=20, padx=20)
        ctk.CTkButton(self, text="OK", command=self.destroy).pack(pady=10)

class GitHubReleaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitHub Release Creator")
        self.geometry("800x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables
        self.github_token = ctk.StringVar(value=config.get('github_token', ''))
        self.repo_owner = ctk.StringVar()
        self.repo_name = ctk.StringVar()
        self.release_tag = ctk.StringVar(value='v3.0.0-alpha')
        self.release_name = ctk.StringVar()
        self.release_description = ctk.StringVar()
        self.asset_file = ''
        self.upload_url = ctk.StringVar(value='')
        self.show_token = False
        self.tooltip = None  # Initialize tooltip as None

        # GUI Setup
        self.create_widgets()

    def create_widgets(self):
        # GitHub Token
        ctk.CTkLabel(self, text="GitHub Token:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.token_entry = ctk.CTkEntry(self, textvariable=self.github_token, width=400, show="*" if not self.show_token else "")
        self.token_entry.grid(row=0, column=1, padx=10, pady=10)
        self.token_entry.bind('<FocusOut>', self.save_token)

        self.create_info_icon("Enter your GitHub token. Required to authenticate requests.", row=0, column=3)

        # Button to Show/Hide Token
        self.toggle_token_button = ctk.CTkButton(self, text="Show/Hide Token", command=self.toggle_token_visibility)
        self.toggle_token_button.grid(row=0, column=2, padx=10, pady=10)

        # Repository Owner/Name
        ctk.CTkLabel(self, text="Repository (Owner/Name):").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.repo_owner, width=180).grid(row=1, column=1, padx=(10, 0), pady=10, sticky='w')
        ctk.CTkEntry(self, textvariable=self.repo_name, width=180).grid(row=1, column=1, padx=(200, 0), pady=10, sticky='w')
        
        self.create_info_icon("Enter the repository owner and name. Format: owner/repository.", row=1, column=3)

        # Upload URL
        ctk.CTkLabel(self, text="Upload URL:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.url_label = ctk.CTkLabel(self, textvariable=self.upload_url, width=400)
        self.url_label.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        # Release Tag
        ctk.CTkLabel(self, text="Release Tag:").grid(row=3, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_tag, width=400).grid(row=3, column=1, padx=10, pady=10)
        
        self.create_info_icon("Enter the release tag (e.g., v1.0.0).", row=3, column=3)

        # Release Name
        ctk.CTkLabel(self, text="Release Name:").grid(row=4, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_name, width=400).grid(row=4, column=1, padx=10, pady=10)
        
        self.create_info_icon("Provide a name for the release.", row=4, column=3)

        # Release Description
        ctk.CTkLabel(self, text="Description:").grid(row=5, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_description, width=400).grid(row=5, column=1, padx=10, pady=10)
        
        self.create_info_icon("Write a description of the release.", row=5, column=3)

        # Select File
        ctk.CTkButton(self, text="Select File", command=self.select_file).grid(row=6, column=0, padx=10, pady=10)
        self.file_label = ctk.CTkLabel(self, text="No file selected", width=400)
        self.file_label.grid(row=6, column=1, padx=10, pady=10, sticky='w')
        
        self.create_info_icon("Select a file to upload as an asset.", row=6, column=3)

        # Button to create release
        ctk.CTkButton(self, text="Create Release", command=self.create_release).grid(row=7, column=1, padx=10, pady=20)

    def create_info_icon(self, text, row, column):
        info_icon = ctk.CTkLabel(self, text="ℹ️", cursor="hand2")
        info_icon.grid(row=row, column=column, padx=10, pady=10)
        info_icon.bind("<Enter>", lambda e: self.show_tooltip(e, text))
        info_icon.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event, text):
        self.tooltip = Tooltip(event.widget, text)

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def toggle_token_visibility(self):
        self.show_token = not self.show_token
        self.token_entry.configure(show="" if self.show_token else "*")

    def save_token(self, event):
        config['github_token'] = self.github_token.get()
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    def select_file(self):
        self.asset_file = filedialog.askopenfilename()
        if self.asset_file:
            self.file_label.configure(text=os.path.basename(self.asset_file))

    def create_release(self):
        token = self.github_token.get()
        if not token:
            CTkMessagebox(title="Error", message="GitHub token is required.")
            return

        owner = self.repo_owner.get()
        repo = self.repo_name.get()
        if not owner or not repo:
            CTkMessagebox(title="Error", message="Repository owner and name are required.")
            return

        # Update URL
        repo_url = f"https://github.com/{owner}/{repo}"
        self.upload_url.set(repo_url)

        # Release data
        data = {
            "tag_name": self.release_tag.get(),
            "name": self.release_name.get(),
            "body": self.release_description.get(),
            "draft": False,
            "prerelease": False
        }

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        # Create release
        response = requests.post(f"https://api.github.com/repos/{owner}/{repo}/releases", json=data, headers=headers)

        if response.status_code == 201:
            release = response.json()
            CTkMessagebox(title="Success", message="Release created successfully.")
            if self.asset_file:
                self.upload_asset(release['upload_url'].split("{")[0], token)
        else:
            CTkMessagebox(title="Error", message=f"Failed to create release: {response.json()}")

    def upload_asset(self, upload_url, token):
        headers = {
            "Authorization": f"token {token}",
            "Content-Type": "application/octet-stream"
        }
        params = {'name': os.path.basename(self.asset_file)}
        with open(self.asset_file, 'rb') as f:
            response = requests.post(upload_url, headers=headers, params=params, data=f)
        if response.status_code == 201:
            CTkMessagebox(title="Success", message="Asset uploaded successfully.")
        else:
            CTkMessagebox(title="Error", message=f"Failed to upload asset: {response.json()}")

if __name__ == "__main__":
    app = GitHubReleaseApp()
    app.mainloop()
