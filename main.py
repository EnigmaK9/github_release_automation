import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import json
import requests
import logging
import zipfile

# Initial interface configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Path to the configuration file
CONFIG_FILE = "config.json"

# Configure logging
logging.basicConfig(level=logging.INFO)

# Tooltip class for information icons
class Tooltip(ctk.CTkToplevel):
    def __init__(self, widget, text):
        super().__init__(widget)
        self.widget = widget
        self.text = text
        self.wm_overrideredirect(True)
        self.label = ctk.CTkLabel(self, text=self.text, justify="left", wraplength=300)
        self.label.pack(ipadx=5, ipady=5)
        self.position_tooltip()

        # Bind events to detect when the mouse leaves the widget
        self.widget.bind("<Leave>", self.hide_tooltip)
        self.widget.bind("<Motion>", self.follow_mouse)

    def position_tooltip(self):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + 20
        self.wm_geometry(f"+{x}+{y}")

    def hide_tooltip(self, event=None):
        self.destroy()

    def follow_mouse(self, event):
        # Update the position of the tooltip
        x = event.x_root + 20
        y = event.y_root + 20
        self.wm_geometry(f"+{x}+{y}")

class JFrogUploader:
    def __init__(self, jfrog_url, jfrog_token, repository):
        self.jfrog_url = jfrog_url.rstrip('/')
        self.jfrog_token = jfrog_token
        self.repository = repository
        self.headers = {
            'Authorization': f'Bearer {self.jfrog_token}'
        }

    def upload_artifact(self, file_path):
        artifact_name = os.path.basename(file_path)
        upload_url = f"{self.jfrog_url}/artifactory/{self.repository}/{artifact_name}"

        with open(file_path, 'rb') as f:
            response = requests.put(upload_url, data=f, headers=self.headers)
            if response.status_code in (200, 201):
                logging.info(f"Successfully uploaded '{artifact_name}' to JFrog repository '{self.repository}'")
                tk.messagebox.showinfo("Success", f"File '{artifact_name}' uploaded to JFrog successfully!")
            else:
                logging.error(f"Failed to upload '{artifact_name}' to JFrog: HTTP {response.status_code}")
                logging.error(f"Response: {response.text}")
                tk.messagebox.showerror("Error", f"Failed to upload to JFrog: {response.text}")
                raise Exception(f"Failed to upload '{artifact_name}' to JFrog: HTTP {response.status_code}")

class GitHubUploaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Ford Release Uploader")
        # Window size
        self.geometry("1200x750")

        # Input variables
        self.directory_path = tk.StringVar()
        self.zip_path = tk.StringVar()
        self.gh_token = tk.StringVar()
        self.repo_owner = tk.StringVar()
        self.repo_name = tk.StringVar()
        self.release_tag = tk.StringVar(value='v1.0.0')
        self.release_name = tk.StringVar()
        self.release_description = tk.StringVar()
        self.target_commitish = tk.StringVar(value='main')
        self.discussion_category_name = tk.StringVar()
        self.generate_release_notes = tk.BooleanVar()
        self.make_latest = tk.StringVar(value='true')
        self.is_prerelease = tk.BooleanVar()

        self.jfrog_token = tk.StringVar()
        self.jfrog_url = tk.StringVar(value='https://ford.jfrog.io')
        self.jfrog_repo = tk.StringVar()
        self.jfrog_url_preview = tk.StringVar()
        self.github_url_preview = tk.StringVar()

        # Load configuration if it exists
        self.load_config()

        # Create graphical interface
        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Create two columns
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Left Column - GitHub Section
        left_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(left_frame, text="GitHub Settings", font=("Arial", 16)).grid(row=0, column=0, columnspan=3, pady=10)

        # GitHub Token
        ctk.CTkLabel(left_frame, text="GitHub Token:").grid(row=1, column=0, sticky="e")
        gh_token_entry = ctk.CTkEntry(left_frame, textvariable=self.gh_token, show="*")
        gh_token_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.create_info_icon(left_frame, "Enter your GitHub personal access token.", row=1, column=2)

        # Repository Owner
        ctk.CTkLabel(left_frame, text="Repository Owner:").grid(row=2, column=0, sticky="e")
        repo_owner_entry = ctk.CTkEntry(left_frame, textvariable=self.repo_owner)
        repo_owner_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.repo_owner.trace_add('write', self.update_github_url_preview)

        # Repository Name
        ctk.CTkLabel(left_frame, text="Repository Name:").grid(row=3, column=0, sticky="e")
        repo_name_entry = ctk.CTkEntry(left_frame, textvariable=self.repo_name)
        repo_name_entry.grid(row=3, column=1, sticky="ew", pady=5)
        self.repo_name.trace_add('write', self.update_github_url_preview)

        self.create_info_icon(left_frame, "Enter the repository owner and name.", row=3, column=2)

        # GitHub URL Preview
        ctk.CTkLabel(left_frame, text="Repository URL:").grid(row=4, column=0, sticky="e")
        github_url_label = ctk.CTkLabel(left_frame, textvariable=self.github_url_preview)
        github_url_label.grid(row=4, column=1, sticky="w", pady=5)

        # Release Tag
        ctk.CTkLabel(left_frame, text="Release Tag:").grid(row=5, column=0, sticky="e")
        release_tag_entry = ctk.CTkEntry(left_frame, textvariable=self.release_tag)
        release_tag_entry.grid(row=5, column=1, sticky="ew", pady=5)

        release_tag_tooltip = (
            "Tagging suggestions\n"
            "It's common practice to prefix your version names with the letter v. "
            "Some good tag names might be v1.0.0 or v2.3.4.\n"
            "If the tag isn't meant for production use, add a pre-release version after the version name. "
            "Some good pre-release versions might be v0.2.0-alpha or v5.9-beta.3.\n\n"
            "Semantic versioning\n"
            "If you're new to releasing software, we highly recommend learning more about semantic versioning."
        )
        self.create_info_icon(left_frame, release_tag_tooltip, row=5, column=2)

        # Release Name
        ctk.CTkLabel(left_frame, text="Release Name:").grid(row=6, column=0, sticky="e")
        release_name_entry = ctk.CTkEntry(left_frame, textvariable=self.release_name)
        release_name_entry.grid(row=6, column=1, sticky="ew", pady=5)

        # Release Description
        ctk.CTkLabel(left_frame, text="Release Description:").grid(row=7, column=0, sticky="e")
        release_desc_entry = ctk.CTkEntry(left_frame, textvariable=self.release_description)
        release_desc_entry.grid(row=7, column=1, sticky="ew", pady=5)

        # Target Commitish
        ctk.CTkLabel(left_frame, text="Target Commitish:").grid(row=8, column=0, sticky="e")
        target_commitish_entry = ctk.CTkEntry(left_frame, textvariable=self.target_commitish)
        target_commitish_entry.grid(row=8, column=1, sticky="ew", pady=5)
        self.create_info_icon(left_frame, "Specify the branch or commit SHA for the release. Default is 'main'.", row=8, column=2)

        # Discussion Category Name
        ctk.CTkLabel(left_frame, text="Discussion Category Name:").grid(row=9, column=0, sticky="e")
        discussion_category_entry = ctk.CTkEntry(left_frame, textvariable=self.discussion_category_name)
        discussion_category_entry.grid(row=9, column=1, sticky="ew", pady=5)
        self.create_info_icon(left_frame, "Specify the discussion category if you want to create a discussion for the release.", row=9, column=2)

        # Generate Release Notes
        ctk.CTkCheckBox(left_frame, text="Generate Release Notes", variable=self.generate_release_notes).grid(row=10, column=1, sticky="w", pady=5)

        # Make Latest
        ctk.CTkLabel(left_frame, text="Make Latest:").grid(row=11, column=0, sticky="e")
        make_latest_options = ["true", "false", "legacy"]
        make_latest_menu = ctk.CTkOptionMenu(
            left_frame, 
            variable=self.make_latest, 
            values=make_latest_options, 
            fg_color="#1F77FF"  # Blue color to match other elements
        )
        make_latest_menu.grid(row=11, column=1, sticky="w", pady=5)
        self.create_info_icon(left_frame, "Specify if this release should be the latest. Options: true, false, legacy.", row=11, column=2)

        # Pre-release Checkbox
        ctk.CTkCheckBox(left_frame, text="Pre-release", variable=self.is_prerelease).grid(row=12, column=1, sticky="w", pady=5)

        ctk.CTkButton(
        left_frame, 
        text="Upload to GitHub", 
        command=self.upload_to_github, 
        fg_color="#1F77FF"  # GitHub Blue Color
        ).grid(row=13, column=0, columnspan=3, pady=10)

        # Right Column - JFrog Section
        right_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(right_frame, text="JFrog Settings", font=("Arial", 16)).grid(row=0, column=0, columnspan=3, pady=10)

        # JFrog Token
        ctk.CTkLabel(right_frame, text="JFrog Token:").grid(row=1, column=0, sticky="e")
        jfrog_token_entry = ctk.CTkEntry(right_frame, textvariable=self.jfrog_token, show="*")
        jfrog_token_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.create_info_icon(right_frame, "Enter your JFrog API token.", row=1, column=2)

        # JFrog URL
        ctk.CTkLabel(right_frame, text="JFrog URL:").grid(row=2, column=0, sticky="e")
        jfrog_url_entry = ctk.CTkEntry(right_frame, textvariable=self.jfrog_url)
        jfrog_url_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.jfrog_url.trace_add('write', self.update_jfrog_url_preview)
        self.create_info_icon(right_frame, "Enter the base URL for your JFrog Artifactory instance.", row=2, column=2)

        # JFrog Repository
        ctk.CTkLabel(right_frame, text="JFrog Repository:").grid(row=3, column=0, sticky="e")
        jfrog_repo_entry = ctk.CTkEntry(right_frame, textvariable=self.jfrog_repo)
        jfrog_repo_entry.grid(row=3, column=1, sticky="ew", pady=5)
        self.jfrog_repo.trace_add('write', self.update_jfrog_url_preview)

        # JFrog URL Preview
        ctk.CTkLabel(right_frame, text="Artifact URL:").grid(row=4, column=0, sticky="e")
        jfrog_url_label = ctk.CTkLabel(right_frame, textvariable=self.jfrog_url_preview)
        jfrog_url_label.grid(row=4, column=1, sticky="w", pady=5)

        ctk.CTkButton(
        right_frame, 
        text="Upload to JFrog", 
        command=self.upload_to_jfrog, 
        fg_color="green"
        ).grid(row=5, column=0, columnspan=3, pady=10)

        ctk.CTkButton(
        main_frame, 
        text="Select Directory to Compress", 
        command=self.select_directory, 
        fg_color="#1F77FF"  # Blue color similar to other buttons
        ).grid(row=1, column=0, columnspan=2, pady=10)

        # Selected Directory Label
        selected_directory_label = ctk.CTkLabel(main_frame, textvariable=self.directory_path)
        selected_directory_label.grid(row=2, column=0, columnspan=2, pady=5)

        # save config button
        ctk.CTkButton(
        main_frame, 
        text="Save Config", 
        command=self.save_config, 
        fg_color="#1F77FF"  # Blue color similar to the other buttons
        ).grid(row=3, column=0, columnspan=2, pady=10)

    def create_info_icon(self, parent, text, row, column):
        info_icon = ctk.CTkLabel(parent, text="ℹ️", cursor="hand2")
        info_icon.grid(row=row, column=column, padx=5)
        info_icon.bind("<Enter>", lambda e: self.show_tooltip(e, text))
        info_icon.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event, text):
        self.tooltip = Tooltip(event.widget, text)

    def hide_tooltip(self, event=None):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.hide_tooltip()
            self.tooltip = None

    def select_directory(self):
        try:
            # Open dialog to select directory
            directory = filedialog.askdirectory()
            if directory:
                self.directory_path.set(directory)
                # Compress the selected directory
                zip_filename = os.path.basename(directory.rstrip('/\\')) + '.zip'
                self.zip_path.set(os.path.join(os.getcwd(), zip_filename))
                with zipfile.ZipFile(self.zip_path.get(), 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(directory):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zipf.write(file_path, os.path.relpath(file_path, directory))
                tk.messagebox.showinfo("Success", f"Directory compressed to '{zip_filename}' successfully.")
            else:
                tk.messagebox.showwarning("Warning", "No directory selected.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"An error occurred while compressing the directory: {str(e)}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.gh_token.set(config.get("gh_token", ""))
                    self.repo_owner.set(config.get("repo_owner", ""))
                    self.repo_name.set(config.get("repo_name", ""))
                    self.release_tag.set(config.get("release_tag", "v1.0.0"))
                    self.release_name.set(config.get("release_name", ""))
                    self.release_description.set(config.get("release_description", ""))
                    self.target_commitish.set(config.get("target_commitish", "main"))
                    self.discussion_category_name.set(config.get("discussion_category_name", ""))
                    self.generate_release_notes.set(config.get("generate_release_notes", False))
                    self.make_latest.set(config.get("make_latest", "true"))
                    self.is_prerelease.set(config.get("is_prerelease", False))

                    self.jfrog_token.set(config.get("jfrog_token", ""))
                    self.jfrog_url.set(config.get("jfrog_url", "https://ford.jfrog.io"))
                    self.jfrog_repo.set(config.get("jfrog_repo", ""))
            except json.JSONDecodeError:
                tk.messagebox.showerror("Error", "Failed to load configuration: Invalid JSON format.")
            except Exception as e:
                tk.messagebox.showerror("Error", f"An error occurred while loading configuration: {str(e)}")

    def save_config(self):
        try:
            config = {
                "gh_token": self.gh_token.get(),
                "repo_owner": self.repo_owner.get(),
                "repo_name": self.repo_name.get(),
                "release_tag": self.release_tag.get(),
                "release_name": self.release_name.get(),
                "release_description": self.release_description.get(),
                "target_commitish": self.target_commitish.get(),
                "discussion_category_name": self.discussion_category_name.get(),
                "generate_release_notes": self.generate_release_notes.get(),
                "make_latest": self.make_latest.get(),
                "is_prerelease": self.is_prerelease.get(),

                "jfrog_token": self.jfrog_token.get(),
                "jfrog_url": self.jfrog_url.get(),
                "jfrog_repo": self.jfrog_repo.get(),
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(config, f)
            tk.messagebox.showinfo("Saved", "Configuration saved successfully!")
        except Exception as e:
            tk.messagebox.showerror("Error", f"An error occurred while saving configuration: {str(e)}")

    def upload_to_github(self):
        if not all([self.gh_token.get(), self.repo_owner.get(), self.repo_name.get(), self.release_tag.get(), self.zip_path.get()]):
            tk.messagebox.showerror("Error", "All GitHub fields are required.")
            return

        headers = {"Authorization": f"token {self.gh_token.get()}"}
        data = {
            "tag_name": self.release_tag.get(),
            "target_commitish": self.target_commitish.get(),
            "name": self.release_name.get(),
            "body": self.release_description.get(),
            "draft": False,
            "prerelease": self.is_prerelease.get(),
            "discussion_category_name": self.discussion_category_name.get() or None,
            "generate_release_notes": self.generate_release_notes.get(),
            "make_latest": self.make_latest.get()
        }
        repo_url = f"https://api.github.com/repos/{self.repo_owner.get()}/{self.repo_name.get()}/releases"

        # Remove keys with None values
        data = {k: v for k, v in data.items() if v is not None}

        try:
            # Create the release on GitHub
            response = requests.post(repo_url, headers=headers, json=data)
            if response.status_code == 422:
                # The release already exists, get its ID
                releases = requests.get(repo_url, headers=headers).json()
                release = next((r for r in releases if r['tag_name'] == self.release_tag.get()), None)
                if release:
                    release_id = release['id']
                else:
                    tk.messagebox.showerror("Error", "Release already exists, but could not retrieve its ID.")
                    return
            else:
                response.raise_for_status()
                release_data = response.json()
                release_id = release_data["id"]

            # Upload the asset
            upload_url = f"https://uploads.github.com/repos/{self.repo_owner.get()}/{self.repo_name.get()}/releases/{release_id}/assets"
            upload_params = {"name": os.path.basename(self.zip_path.get())}
            with open(self.zip_path.get(), "rb") as zip_file:
                headers["Content-Type"] = "application/zip"
                upload_response = requests.post(
                    upload_url,
                    headers=headers,
                    params=upload_params,
                    data=zip_file.read()
                )
                upload_response.raise_for_status()
                tk.messagebox.showinfo("Success", "File uploaded to GitHub successfully!")
        except requests.exceptions.HTTPError as e:
            tk.messagebox.showerror("HTTP Error", f"Failed to communicate with GitHub: {str(e)}\n{e.response.text}")
        except requests.exceptions.RequestException as e:
            tk.messagebox.showerror("Request Error", f"An error occurred during upload: {str(e)}")
        except FileNotFoundError:
            tk.messagebox.showerror("File Error", "The ZIP file could not be found.")
        except Exception as e:
            tk.messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    def upload_to_jfrog(self):
        if not all([self.jfrog_token.get(), self.jfrog_url.get(), self.jfrog_repo.get(), self.zip_path.get()]):
            tk.messagebox.showerror("Error", "All JFrog fields are required.")
            return

        try:
            uploader = JFrogUploader(self.jfrog_url.get(), self.jfrog_token.get(), self.jfrog_repo.get())
            uploader.upload_artifact(self.zip_path.get())
        except Exception as e:
            tk.messagebox.showerror("Error", f"Failed to upload to JFrog: {str(e)}")

    def update_github_url_preview(self, *args):
        owner = self.repo_owner.get()
        repo = self.repo_name.get()
        if owner and repo:
            url = f"https://github.com/{owner}/{repo}"
            self.github_url_preview.set(url)
        else:
            self.github_url_preview.set("")

    def update_jfrog_url_preview(self, *args):
        jfrog_url = self.jfrog_url.get().rstrip('/')
        repo = self.jfrog_repo.get()
        if jfrog_url and repo:
            artifact_name = os.path.basename(self.zip_path.get()) if self.zip_path.get() else "<artifact_name>"
            url = f"{jfrog_url}/artifactory/{repo}/{artifact_name}"
            self.jfrog_url_preview.set(url)
        else:
            self.jfrog_url_preview.set("")

if __name__ == "__main__":
    # Start the application
    app = GitHubUploaderApp()
    app.mainloop()
