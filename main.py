import customtkinter as ctk
from tkinter import filedialog
import requests
import json
import os
import zipfile

# Load or create config.json
CONFIG_FILE = 'config.json'
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
else:
    config = {'github_token': ''}

# Load or initialize release data
RELEASE_DATA_FILE = 'release_data.json'
if os.path.exists(RELEASE_DATA_FILE):
    with open(RELEASE_DATA_FILE, 'r') as f:
        release_data = json.load(f)
else:
    release_data = {
        'repo_owner': '',
        'repo_name': '',
        'release_tag': 'v1.0.0',
        'release_name': '',
        'release_description': ''
    }

# Tooltip class
class Tooltip(ctk.CTkToplevel):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.widget = widget
        self.text = text
        self.wm_overrideredirect(True)
        self.label = ctk.CTkLabel(self, text=self.text, justify="left", wraplength=300)
        self.label.pack(ipadx=5, ipady=5)
        self.position_tooltip()

        # Bind to the widget to detect when the mouse leaves
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.follow_mouse)

    def position_tooltip(self):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self, event):
        self.destroy()

    def follow_mouse(self, event):
        # Update the position of the tooltip
        x = event.x_root + 20
        y = event.y_root + 20
        self.wm_geometry(f"+{x}+{y}")

# Custom message box using CTkToplevel
class CTkMessagebox(ctk.CTkToplevel):
    def __init__(self, title="Message", message="This is a message"):
        super().__init__()

        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)
        self.grab_set()  # Set focus on this window

        ctk.CTkLabel(self, text=message, wraplength=350, justify="left").pack(pady=20, padx=20)
        ctk.CTkButton(self, text="OK", command=self.destroy).pack(pady=10)

class GitHubReleaseApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitHub Release Creator")
        self.geometry("840x600")
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        # Variables
        self.github_token = ctk.StringVar(value=config.get('github_token', ''))
        self.repo_owner = ctk.StringVar(value=release_data.get('repo_owner', ''))
        self.repo_name = ctk.StringVar(value=release_data.get('repo_name', ''))
        self.release_tag = ctk.StringVar(value=release_data.get('release_tag', 'v1.0.0'))
        self.release_name = ctk.StringVar(value=release_data.get('release_name', ''))
        self.release_description = ctk.StringVar(value=release_data.get('release_description', ''))
        self.asset_file = ''
        self.upload_url = ctk.StringVar(value='')
        self.show_token = False
        self.tooltip = None  # Initialize tooltip as None
        self.directory = ''  # Selected directory

        # Interface setup
        self.create_widgets()

    def create_widgets(self):
        # GitHub Token
        ctk.CTkLabel(self, text="GitHub Token:").grid(row=0, column=0, padx=10, pady=10, sticky='e')
        self.token_entry = ctk.CTkEntry(self, textvariable=self.github_token, width=400, show="*" if not self.show_token else "")
        self.token_entry.grid(row=0, column=1, padx=10, pady=10)
        self.token_entry.bind('<FocusOut>', self.save_token)

        self.create_info_icon("Enter your GitHub token. Required to authenticate requests.", row=0, column=3)

        # Button to show/hide the token
        self.toggle_token_button = ctk.CTkButton(self, text="Show/Hide Token", command=self.toggle_token_visibility)
        self.toggle_token_button.grid(row=0, column=2, padx=10, pady=10)

        # Repository owner and name
        ctk.CTkLabel(self, text="Repository Owner:").grid(row=1, column=0, padx=10, pady=10, sticky='e')
        self.repo_owner_entry = ctk.CTkEntry(self, textvariable=self.repo_owner, width=180)
        self.repo_owner_entry.grid(row=1, column=1, padx=(10, 0), pady=10, sticky='w')
        self.repo_owner.trace_add('write', self.update_repo_url)

        ctk.CTkLabel(self, text="Repository Name:").grid(row=1, column=1, padx=(200, 0), pady=10, sticky='e')
        self.repo_name_entry = ctk.CTkEntry(self, textvariable=self.repo_name, width=180)
        self.repo_name_entry.grid(row=1, column=1, padx=(310, 0), pady=10, sticky='w')
        self.repo_name.trace_add('write', self.update_repo_url)

        self.create_info_icon("Enter the repository owner and name.", row=1, column=3)

        # Repository URL preview
        ctk.CTkLabel(self, text="Repository URL:").grid(row=2, column=0, padx=10, pady=10, sticky='e')
        self.url_label = ctk.CTkLabel(self, textvariable=self.upload_url, width=400)
        self.url_label.grid(row=2, column=1, padx=10, pady=10, sticky='w')

        # Release Tag
        ctk.CTkLabel(self, text="Release Tag:").grid(row=3, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_tag, width=400).grid(row=3, column=1, padx=10, pady=10)

        # Updated tooltip for Release Tag
        release_tag_tooltip = (
            "Tagging suggestions\n"
            "It’s common practice to prefix your version names with the letter v. Some good tag names might be v1.0.0 or v2.3.4.\n"
            "If the tag isn’t meant for production use, add a pre-release version after the version name. Some good pre-release versions might be v0.2.0-alpha or v5.9-beta.3.\n\n"
            "Semantic versioning\n"
            "If you're new to releasing software, we highly recommend learning more about semantic versioning.\n"
            "A newly published release will automatically be labeled as the latest release for this repository.\n"
            "If 'Set as the latest release' is unchecked, the latest release will be determined by higher semantic version and creation date."
        )
        self.create_info_icon(release_tag_tooltip, row=3, column=3)

        # Release Name
        ctk.CTkLabel(self, text="Release Name:").grid(row=4, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_name, width=400).grid(row=4, column=1, padx=10, pady=10)

        self.create_info_icon("Provide a name for the release.", row=4, column=3)

        # Release Description
        ctk.CTkLabel(self, text="Description:").grid(row=5, column=0, padx=10, pady=10, sticky='e')
        ctk.CTkEntry(self, textvariable=self.release_description, width=400).grid(row=5, column=1, padx=10, pady=10)

        self.create_info_icon("Write a description for the release.", row=5, column=3)

        # Select Directory
        ctk.CTkButton(self, text="Select Directory", command=self.select_directory).grid(row=6, column=0, padx=10, pady=10)
        self.file_label = ctk.CTkLabel(self, text="No directory selected", width=400)
        self.file_label.grid(row=6, column=1, padx=10, pady=10, sticky='w')

        self.create_info_icon("Select a directory to compress and upload as an asset.", row=6, column=3)

        # Button to create the release
        ctk.CTkButton(self, text="Create Release", command=self.create_release).grid(row=7, column=1, padx=10, pady=20)

        # Initialize repository URL
        self.update_repo_url()

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

    def select_directory(self):
        self.directory = filedialog.askdirectory()
        if self.directory:
            # Compress the directory into a zip file
            zip_filename = os.path.basename(self.directory.rstrip('/\\')) + '.zip'
            self.asset_file = os.path.join(os.getcwd(), zip_filename)
            with zipfile.ZipFile(self.asset_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(self.directory):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, self.directory))
            self.file_label.configure(text=zip_filename)

    def update_repo_url(self, *args):
        owner = self.repo_owner.get()
        repo = self.repo_name.get()
        if owner and repo:
            repo_url = f"https://github.com/{owner}/{repo}"
            self.upload_url.set(repo_url)
        else:
            self.upload_url.set('')

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

            # Save successful release data
            self.save_release_data()

            if self.asset_file and os.path.exists(self.asset_file):
                self.upload_asset(release['upload_url'].split("{")[0], token)
            else:
                CTkMessagebox(title="Error", message="No asset file to upload.")
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
            # Optionally delete the asset file after upload
            # os.remove(self.asset_file)
        else:
            CTkMessagebox(title="Error", message=f"Failed to upload asset: {response.json()}")

    def save_release_data(self):
        release_data = {
            'repo_owner': self.repo_owner.get(),
            'repo_name': self.repo_name.get(),
            'release_tag': self.release_tag.get(),
            'release_name': self.release_name.get(),
            'release_description': self.release_description.get()
        }
        with open(RELEASE_DATA_FILE, 'w') as f:
            json.dump(release_data, f)

if __name__ == "__main__":
    app = GitHubReleaseApp()
    app.mainloop()
