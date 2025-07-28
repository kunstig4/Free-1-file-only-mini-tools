import os
import sys
import json
import subprocess
import requests
import re

# --- Configuration ---
# The name for the server jar file.
SERVER_JAR_NAME = "server.jar"
# Default RAM allocation for the server (e.g., "2G" for 2 Gigabytes).
DEFAULT_RAM = "2G"
# URL to fetch Minecraft version manifest.
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def get_latest_server_url():
    """Fetches the download URL for the latest stable Minecraft server version."""
    try:
        print("Fetching latest version information from Mojang...")
        manifest_response = requests.get(VERSION_MANIFEST_URL)
        manifest_response.raise_for_status()
        manifest = manifest_response.json()
        
        latest_stable = manifest['latest']['release']
        print(f"Latest stable version is: {latest_stable}")

        version_url = next((v['url'] for v in manifest['versions'] if v['id'] == latest_stable), None)
        if not version_url:
            print(f"Error: Could not find URL for version {latest_stable}.")
            return None

        version_data_response = requests.get(version_url)
        version_data_response.raise_for_status()
        version_data = version_data_response.json()
        
        server_download_url = version_data.get('downloads', {}).get('server', {}).get('url')
        if not server_download_url:
            print("Error: Server download URL not found in version data.")
            return None
            
        return server_download_url
    except requests.exceptions.RequestException as e:
        print(f"Error fetching version data: {e}")
        return None
    except KeyError:
        print("Error parsing version manifest. The structure might have changed.")
        return None


def download_server(url):
    """Downloads the server jar file if it doesn't already exist."""
    if os.path.exists(SERVER_JAR_NAME):
        print(f"'{SERVER_JAR_NAME}' already exists. Skipping download.")
        return True
    
    print(f"Downloading '{SERVER_JAR_NAME}' from {url}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(SERVER_JAR_NAME, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print("Download complete.")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading server: {e}")
        return False

def handle_eula():
    """Checks for eula.txt and prompts the user to accept it."""
    if not os.path.exists('eula.txt'):
        print("\nEULA file not found.")
        print("You need to accept the Minecraft EULA to run the server.")
        print("Running the server once to generate the EULA file...")
        
        # Run once to generate files
        try:
            subprocess.run(['java', '-jar', SERVER_JAR_NAME, 'nogui'], timeout=30)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            print("Server stopped. EULA file should now be present.")
        except FileNotFoundError:
            print("\nError: 'java' command not found.")
            print("Please make sure you have Java installed and in your system's PATH.")
            sys.exit(1)


    try:
        with open('eula.txt', 'r') as f:
            content = f.read()

        if 'eula=true' in content:
            print("EULA already accepted.")
            return True

        print("\n----------------------------------------------------")
        print("Minecraft End User License Agreement (EULA)")
        print("By continuing, you are indicating your agreement to the EULA.")
        print("You can read the EULA at: https://account.mojang.com/documents/minecraft_eula")
        
        choice = input("Do you accept the EULA? (yes/no): ").lower()
        
        if choice in ['yes', 'y']:
            with open('eula.txt', 'w') as f:
                f.write('eula=true\n')
            print("EULA accepted.")
            return True
        else:
            print("You must accept the EULA to run the server.")
            return False
    except FileNotFoundError:
        print("eula.txt not found after initial run. Please run the server manually once.")
        return False


def start_server():
    """Starts the Minecraft server with a specified amount of RAM."""
    ram_alloc = input(f"Enter RAM to allocate (e.g., 2G, 1024M) [default: {DEFAULT_RAM}]: ").strip()
    if not ram_alloc:
        ram_alloc = DEFAULT_RAM

    if not re.match(r'^\d+[MG]$', ram_alloc, re.IGNORECASE):
        print(f"Invalid RAM format. Using default: {DEFAULT_RAM}")
        ram_alloc = DEFAULT_RAM
        
    start_command = [
        'java',
        f'-Xmx{ram_alloc}',
        f'-Xms{ram_alloc}',
        '-jar',
        SERVER_JAR_NAME,
        'nogui'
    ]
    
    print("\nStarting server with command:")
    print(f"  {' '.join(start_command)}")
    print("To stop the server, type 'stop' in the console that appears.")
    print("----------------------------------------------------\n")
    
    try:
        subprocess.run(start_command)
    except FileNotFoundError:
        print("\nError: 'java' command not found.")
        print("Please make sure you have Java installed and in your system's PATH.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nServer process interrupted by user. Shutting down.")


if __name__ == '__main__':
    print("--- Minecraft Server Manager ---")
    
    # Step 1: Get the latest server URL
    server_url = get_latest_server_url()
    if not server_url:
        sys.exit(1)
        
    # Step 2: Download the server if it's not there
    if not download_server(server_url):
        sys.exit(1)
        
    # Step 3: Handle the EULA agreement
    if not handle_eula():
        sys.exit(1)
        
    # Step 4: Start the server
    start_server()
    
    print("\nServer process finished.")
