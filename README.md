﻿## README.md


# GitHub Release Creator

This is a Python application with a graphical user interface (GUI) that allows you to select a directory, compress its contents into a `.zip` file, and upload it to GitHub as a release asset. The program also saves your release data to streamline future releases.

## Features

- **Select Directory**: Choose a directory to compress and upload.
- **Create Release**: Automatically create a GitHub release with the provided information.
- **Upload Asset**: Upload the compressed `.zip` file as an asset to the release.
- **Data Persistence**: Saves your release data for easier future releases.
- **Dynamic URL Preview**: Displays the repository URL dynamically as you input the owner and repository name.
- **Tooltips**: Provides helpful information via tooltips when hovering over information icons.

## Prerequisites

- **Python 3.6 or higher**
- **GitHub Personal Access Token**: Must have permissions to create releases and upload assets (usually the `repo` scope).

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your_username/your_repository.git
   cd your_repository
   ```


2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   or you can install the dependencies directly:

   ```bash
   pip install customtkinter requests
   ```

## Usage

1. **Run the Application**

   ```bash
   python github_release_automation.py
   ```

2. **Enter GitHub Token**

   - Input your GitHub personal access token in the "GitHub Token" field.
   - The token is required to authenticate requests to GitHub's API.
   - **Security Note**: The token is saved in `config.json` for convenience. Ensure this file is kept secure and is included in `.gitignore`.

3. **Fill in Repository Details**

   - **Repository Owner**: Your GitHub username or organization name.
   - **Repository Name**: The name of your GitHub repository.
   - The "Repository URL" will update dynamically to reflect the full URL.

4. **Review Release Tag Suggestions**

   - Hover over the information icon next to "Release Tag" to read tagging suggestions and semantic versioning information.

5. **Fill in Release Details**

   - **Release Tag**: Follows the format `v1.0.0`. Adjust as needed.
   - **Release Name**: A descriptive name for your release.
   - **Description**: Detailed information about the release.

6. **Select Directory**

   - Click "Select Directory" to choose the directory you want to compress and upload.
   - The selected directory will be compressed into a `.zip` file.

7. **Create Release**

   - Click "Create Release" to create the release on GitHub.
   - The compressed directory will be uploaded as an asset to the release.
   - Upon success, your release data will be saved for future use.

8. **Data Persistence**

   - After a successful release, your input data (excluding the GitHub token) is saved to `release_data.json`.
   - The next time you run the application, these fields will be pre-filled.

## Important Notes

- **Token Security**

  - Your GitHub token is sensitive information.
  - Ensure `config.json` and `release_data.json` are included in `.gitignore` to prevent accidental commits.
  - Do not share these files publicly.

- **Error Handling**

  - The application provides error messages if required fields are missing or if API requests fail.
  - Ensure all fields are correctly filled before creating a release.

- **Dependencies**

  - The application uses `customtkinter` for the GUI and `requests` for HTTP requests.
  - Ensure these packages are installed.

- **Asset File Cleanup**

  - If you wish to delete the generated `.zip` file after uploading, uncomment the line `# os.remove(self.asset_file)` in the `upload_asset` method.

## Troubleshooting

- **Module Not Found Error**

  - Ensure all dependencies are installed.
  - Run `pip install customtkinter requests` to install missing packages.

- **Authentication Errors**

  - Verify that your GitHub token is correct and has the necessary permissions.

- **API Rate Limits**

  - Be aware of GitHub's API rate limits, especially if making multiple requests in a short period.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern GUI components.
- [Requests](https://requests.readthedocs.io/en/latest/) for making HTTP requests simple.

## Contact

For any questions or issues, please open an issue on the repository or contact [your_email@example.com](mailto:your_email@example.com).

````

---

## .gitignore

```gitignore
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Packages
*.egg
*.egg-info/
dist/
build/
eggs/
parts/
bin/
var/
sdist/
develop-eggs/
.installed.cfg
lib/
lib64/
__pypackages__/

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# macOS files
.DS_Store

# Windows files
Thumbs.db
ehthumbs.db
Desktop.ini

# Zip files
*.zip

# Sensitive configuration files
config.json
release_data.json

# Logs and databases
*.log
*.sql
*.sqlite

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
coverage.xml
*.cover

# Jupyter Notebook checkpoints
.ipynb_checkpoints

# PyCharm
.idea/

# Visual Studio Code
.vscode/

# Sublime Text
*.sublime-project
*.sublime-workspace

# Pytest cache
.pytest_cache/

# Temporary files
*.tmp
*.bak
~$*
````
