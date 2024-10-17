from server_utils import *
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
def check_and_install_palguard(palserver_folder, target_path, palguard_enabled, log):
    log("Checking PalGuard...")    
    if not palguard_enabled:
        log("PalGuard is disabled. Skipping installation.")
        return    
    log("Installing PalGuard...")
    palguard_zip = os.path.join(palserver_folder, "PalGuard.zip")    
    if os.path.exists(palguard_zip):
        with zipfile.ZipFile(palguard_zip, 'r') as zip_ref:
            zip_ref.extractall(target_path)
        log("PalGuard installation completed.")
    else:
        log("PalGuard.zip not found. Installation failed.")
def check_and_install_save_tools(palserver_folder, save_tools_folder, log):
    log("Checking SaveTools...")
    retries = 5
    for attempt in range(retries):
        if os.path.exists(save_tools_folder):
            try:
                shutil.rmtree(save_tools_folder)
                break
            except PermissionError:
                log("SaveTools folder in use, retrying...")
                time.sleep(1)
    else:
        log("Failed to remove SaveTools folder after multiple attempts.")
        return
    log("Installing SaveTools...")
    save_tools_zip = os.path.join(palserver_folder, "PalworldSaveTools.zip")
    if os.path.exists(save_tools_zip):
        with zipfile.ZipFile(save_tools_zip, 'r') as zip_ref:
            zip_ref.extractall(palserver_folder)
        log("SaveTools installation completed.")
    else:
        log("PalworldSaveTools.zip not found. Installation failed.")    
def install_mods():
    log("Checking mods...")
    if mods_enabled == 0:
        log("Mods are disabled. Skipping installation.")
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
def check_reduce_memory():
    log("Checking Reduce Memory...")
    log("Installing Reduce Memory...")
    reduce_memory_folder = os.path.join(palserver_folder, "ReduceMemory")
    if not os.path.exists(reduce_memory_folder):
        os.makedirs(reduce_memory_folder)
    try:
        extract_zip(os.path.join(palserver_folder, "ReduceMemory.zip"), reduce_memory_folder)
        log("Reduce Memory installation completed.")
    except Exception as e:
        log(f"Error installing Reduce Memory: {e}")        
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
        "PalGuard.zip",
        "PalworldSaveTools.zip",
        "ServerTweaks.zip",
        "Steamcmd.zip",
        "ReduceMemory.zip"
    ]    
    for file_name in deletion_zipped_files:
        file_path = os.path.join(palserver_folder, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
            log(f"Deleted {file_name}")