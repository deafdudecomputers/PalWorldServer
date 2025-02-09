from server_configurations import *
def check_powershell():
    log("Checking PowerShell...")
    try:
        result = subprocess.run(["powershell", "-ExecutionPolicy", "Bypass", "-Command", "exit $PSVersionTable.PSVersion.Major -ge 7"], check=True)
        if result.returncode == 0:
            log("PowerShell 7 or higher is already installed.")
            return True
    except subprocess.CalledProcessError:
        log("PowerShell 7 or higher is required. Installing PowerShell 7...")
    url_windows = "https://github.com/PowerShell/PowerShell/releases/download/v7.2.0/PowerShell-7.2.0-win-x64.msi"
    installer_file = os.path.join(os.getenv('TEMP'), "PowerShellInstaller.msi")
    log(f"Downloading PowerShell 7 installer from {url_windows}...")
    try:
        urllib.request.urlretrieve(url_windows, installer_file)
    except Exception as e:
        log(f"Failed to download PowerShell 7 installer from {url_windows}. Error: {e}")
        return False
    log("Installing PowerShell 7...")
    try:
        subprocess.run(["msiexec", "/i", installer_file, "/quiet", "/qn", "/norestart"], check=True)
        log("PowerShell 7 installed successfully.")
        return True
    except subprocess.CalledProcessError:
        log(f"Failed to install PowerShell 7. Please install it manually from {url_windows}.")
        return False
_PALDEFENDER_LATEST_URL = "https://www.dropbox.com/scl/fi/xfmqdv4rsha2ee73opx5l/PalDefender.zip?rlkey=i9y15rzlgxou3i1i0wrjzdvkk&st=94yyyyar&dl=1"
def check_and_install_paldefender(palserver_folder, target_path, paldefender_enabled, log):
    log("Checking PalDefender...")
    if not paldefender_enabled:
        log("PalDefender is disabled. Skipping installation.")
        return
    log("Installing PalDefender...")
    paldefender_zip = os.path.join(target_path, "PalDefender.zip")
    try:
        log("Downloading PalDefender.zip...")
        response = requests.get(_PALDEFENDER_LATEST_URL, stream=True)
        response.raise_for_status()
        with open(paldefender_zip, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        log(f"Downloaded PalDefender.zip to '{paldefender_zip}'")
        log("Extracting PalDefender.zip...")
        with zipfile.ZipFile(paldefender_zip, 'r') as zip_ref:
            zip_ref.extractall(target_path)
        log(f"Extracted PalDefender to '{target_path}'")
        os.remove(paldefender_zip)
        log("PalDefender installation completed.")
    except requests.exceptions.RequestException as e:
        log(f"Error downloading PalDefender.zip: {e}")
    except zipfile.BadZipFile:
        log("Error: PalDefender.zip is corrupted.")
def install_mods():
    log("Checking mods...")
    if mods_enabled == 0:
        log("Mods are disabled. Skipping installation.")
        try:
            ue4ss_settings = os.path.join(target_path, "UE4SS-settings.ini")
            ue4ss_dll = os.path.join(target_path, "UE4SS.dll")
            for file in [ue4ss_settings, ue4ss_dll]:
                if os.path.exists(file):
                    os.remove(file)
                    log(f"Deleted {file}.")
        except Exception as e:
            log(f"Error deleting UE4SS files: {e}")
        return
    log("Installing mods...")
    try:
        extract_zip(os.path.join(palserver_folder, "Mods.zip"), palserver_folder)
        log("Mods installation completed.")
    except Exception as e:
        log(f"Error installing mods: {e}")
def install_server_tweaks():
    log("Checking server tweaks...")
    if server_tweaks_enabled == 0:
        log("Server tweaks are disabled. Skipping installation.")
        return
    log("Installing server tweaks...")
    try:
        extract_zip(os.path.join(palserver_folder, "ServerTweaks.zip"), palserver_folder)
        log("Server tweaks installation completed.")
    except Exception as e:
        log(f"Error installing server tweaks: {e}")      
def download_and_extract_files(url, dest_folder):
    log("Downloading server files...")
    try:
        response = requests.get(url, stream=True)
        zip_file_path = os.path.join(dest_folder, 'server_files.zip')        
        with open(zip_file_path, 'wb') as f:
            f.write(response.content)        
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(dest_folder)        
        os.remove(zip_file_path)
        log("Server files downloaded and extracted successfully.")
    except Exception as e:
        log(f"Error: Exception while downloading or extracting files. Exception: {e}")
def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
def extract_steamcmd():
    log("Extracting steamcmd...")
    try:
        steamcmd_zip = os.path.join(palserver_folder, 'steamcmd.zip')
        extract_zip(steamcmd_zip, steamcmd_folder)
        log("Steamcmd extracted successfully.")
    except Exception as e:
        log(f"Error: Exception while extracting steamcmd. Exception: {e}")        
def delete_zipped_files(palserver_folder, log):
    deletion_zipped_files = [
        "ServerFiles.zip",
        "Mods.zip",
        "ServerTweaks.zip",
        "Steamcmd.zip"
    ]    
    for file_name in deletion_zipped_files:
        file_path = os.path.join(palserver_folder, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            log(f"Deleted {file_name}")