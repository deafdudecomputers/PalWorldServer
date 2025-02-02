import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ScriptShared.server_utils import *
server_name = "Public" #Edit this for your server "folder name".
batch_title = f"Pylar's {server_name} Server Management" #Do NOT touch this, leave as is.
personalize_message = f"Welcome to {batch_title}..." #Do NOT touch this, leave as is.
game_app_id = 2394010 #Do NOT touch this, leave as is.
loop_time = 1 #Do NOT touch this, leave as is.
process_priority = "AboveNormal" #Gives second to highest priority to the server to access the server's resources.
server_address = "localhost" #Do NOT touch this, leave as is.
admin_password = "PylarServer" #Edit this for your admin password, usable for accessing restapi/rcon functions.
server_password = "" #Edit this for your server password, to only allow players with your server password to be able to get on.
server_rcon_port = 25575 #Edit this for your rcon port.
server_port = 8211 #Edit this for your port.
server_query_port = 27015 #Edit this for your query port.
server_restapi_port = 26015 #Edit this for your restapi port.
base_dir = os.path.dirname(os.path.abspath(__file__))
palserver_folder = os.path.join(base_dir, f"PalServer_{server_name}") #Do NOT touch this, leave as is.
saved_folder = os.path.join(palserver_folder, "Pal", "Saved") #Do NOT touch this, leave as is.
backup_folder = os.path.join(palserver_folder, "Server_Backups") #Do NOT touch this, leave as is.
target_path = os.path.join(palserver_folder, "Pal", "Binaries", "Win64") #Do NOT touch this, leave as is.
server_tweaks_folder = os.path.join(saved_folder, "Config", "WindowsServer") #Do NOT touch this, leave as is.
log_folder = os.path.join(palserver_folder, "ServerManagementLogs") #Do NOT touch this, leave as is.
steamcmd_folder = os.path.join(palserver_folder, "steamcmd") #Do NOT touch this, leave as is.
steamcmd_path = os.path.join(steamcmd_folder, "steamcmd.exe") #Do NOT touch this, leave as is.
windows_server_folder = os.path.join(palserver_folder, "Pal", "Saved", "Config", "WindowsServer") #Do NOT touch this, leave as is.
default_config_file = os.path.join(palserver_folder, "DefaultPalWorldSettings.ini") #Do NOT touch this, leave as is.
config_file = os.path.join(windows_server_folder, "PalWorldSettings.ini") #Do NOT touch this, leave as is.
server_file = os.path.join(windows_server_folder, "GameUserSettings.ini") #Do NOT touch this, leave as is.
engine_file = os.path.join(windows_server_folder, "Engine.ini") #Do NOT touch this, leave as is.
online_file = os.path.join(palserver_folder, "players_online.json") #Do NOT touch this, leave as is.
temp_file = os.path.join(palserver_folder, "temp_players.json") #Do NOT touch this, leave as is.
save_tools_folder = os.path.join(palserver_folder, "PalworldSaveTools") #Do NOT touch this, leave as is.
fix_save = os.path.join(save_tools_folder, "fix_world.cmd") #Do NOT touch this, leave as is.
fixed_save = os.path.join(save_tools_folder, "fixed", "Level.sav") #Do NOT touch this, leave as is.
username = "admin" #Do NOT touch this, leave as is.
password = admin_password #Do NOT touch this, leave as is.
server_files_url = "https://www.dropbox.com/scl/fi/7j4r4zbl6gjt6avnbzchv/ServerFiles.zip?rlkey=2yc0e7pxo8lqy3yxto1asg75u&st=afj22jv3&dl=1" #Do NOT touch this, leave as is.
config_server_name = f"{server_name} Server" #Edit this for your server name.
config_server_desc = f"{server_name} Server" #Edit this for your server desc.
custom_server_address = "" #Do NOT touch this, leave as is.
enable_custom_server_address = 0 #Do NOT touch this, leave as is.
palguard_enabled = 1 #Set to 0 if you do NOT want to install Palguard.
mods_enabled = 1 #Set to 0 if you do NOT want to install mods.
server_tweaks_enabled = 1 #Set to 0 if you do NOT want to reconfigure the engine for better server performance.
is_public = 1 #Set to 0 if you do NOT want to make your server public, aka findable on community server list.
backup_days = 180 #Set to how many days you want to keep backups of. After certain days, the saves by then will be deleted.
palserver_exe_cmd = os.path.join(target_path, "PalServer-Win64-Shipping-Cmd.exe") #Do NOT touch this, leave as is.
palserver_exe_regular = os.path.join(target_path, "PalServer-Win64-Shipping.exe") #Do NOT touch this, leave as is.
palserver_exe_original = os.path.join(palserver_folder, "PalServer.exe") #Do NOT touch this, leave as is.
palserver_exe = palserver_exe_regular #Do NOT touch this, leave as is.
palserver_exes = [palserver_exe_cmd, palserver_exe_regular, palserver_exe_original] #Do NOT touch this, leave as is.
palguard_json = os.path.join(target_path, "PalGuard", "PalGuard.json") #Do NOT touch this, leave as is.
server_update_enable = 1 #Set to 1 if you want it to update, otherwise set to 0 if you want to disable the updates.
server_update_manifest = 0 #Set to 1 if you want it to update to certain version(manifest), otherwise set to 0 if you want to disable the updates.
disable_reboots = 1 #Set to 1 if you don't want scheduled reboots. Otherwise, set to 0 if you want scheduled reboots.
disable_announcements = 0 #Set to 1 if you don't want announcements. Otherwise, set to 0 if you want announcements.
def get_public_ip():
    response = requests.get("https://icanhazip.com")
    return response.text.strip()
get_public_ip()
add_ips = [get_public_ip(), "127.0.0.1"]
remove_ips = []  
def update_palguard_json():
    updates = {
        "adminAutoLogin": True,
        "allowAdminCheats": True,
        "logChat": True,
        "logNetworking": True,
        "logRCON": True,
        "useWhitelist": False, #set to True to enable whitelisting, which will be required to get on your server.
        "announceConnections": True,
        "bannedMessage": "You've been banned.",
        "announcePunishments": True,
        "disableIllegalItemProtection": False,
        "doActionUponIllegalPalStats" : False,
        "whitelistMessage": f"You need to whitelist at ."
    }
    if os.path.exists(palguard_json):
        with open(palguard_json, 'r') as file:
            data = json.load(file)
    else:
        log(f"Palguard json at: {palguard_json} does not exist.")
        return
    data.update(updates)
    if 'adminIPs' not in data:
        data['adminIPs'] = []
    if add_ips:
        for ip in add_ips:
            if ip not in data['adminIPs']:
                data['adminIPs'].append(ip)
    if remove_ips:
        data['adminIPs'] = [ip for ip in data['adminIPs'] if ip not in remove_ips]
    with open(palguard_json, 'w') as file:
        json.dump(data, file, indent=4)    
    log(f"Successfully updated palguard json at {palguard_json}.")
def update_engine_file():
    log("Updating the engine file, please wait...")
    search_replace_pairs = {
        "NetServerMaxTickRate=[0-9]+": "NetServerMaxTickRate=120",
        "NetClientTicksPerSecond=[0-9]+": "NetClientTicksPerSecond=15",
        "TimeBetweenPurgingPendingKillObjects=[0-9]+": "TimeBetweenPurgingPendingKillObjects=60",
        r"\[OnlineSubsystemSteam\]\nbEnabled=[a-zA-Z]+": "[OnlineSubsystemSteam]\nbEnabled=True" #False if you use NoSteam, True if you use Steam
    }
    try:
        with open(engine_file, 'r') as file:
            file_contents = file.read()        
        for search_pattern, replacement in search_replace_pairs.items():
            file_contents = re.sub(search_pattern, replacement, file_contents)        
        with open(engine_file, 'w') as file:
            file.write(file_contents)        
        log("Engine file has been updated...")
    except Exception as e:
        log(f"Error: Exception while updating engine file. Exception: {e}")         
def update_palworldsettings_file(config_file, server_restapi_port, server_rcon_port, server_port, admin_password, config_server_name, config_server_desc, server_password, public_ip):
    log("Updating Palworld settings file...")
    replacements = {
        'RESTAPIPort=[0-9]+': f'RESTAPIPort={server_restapi_port}', #Do NOT touch this, leave as is.
        'RCONPort=[0-9]+': f'RCONPort={server_rcon_port}', #Do NOT touch this, leave as is.
        'bIsUseBackupSaveData=[a-zA-Z]+': 'bIsUseBackupSaveData=False', #Do NOT touch this, leave as is. (We have auto backup, so no need to enable this.)
        'RESTAPIEnabled=[a-zA-Z]+': 'RESTAPIEnabled=True',
        'RCONEnabled=[a-zA-Z]+': 'RCONEnabled=True',
        'bShowPlayerList=[a-zA-Z]+': 'bShowPlayerList=True',
        'PublicPort=[0-9]+': f'PublicPort={server_port}', #Do NOT touch this, leave as is.
        'AdminPassword="[^"]*"': f'AdminPassword="{admin_password}"', #Do NOT touch this, leave as is.
        'ServerName="[^"]*"': f'ServerName="{config_server_name}"', #Do NOT touch this, leave as is.
        'ServerDescription="[^"]*"': f'ServerDescription="{config_server_desc}"', #Do NOT touch this, leave as is.
        'ServerPassword="[^"]*"': f'ServerPassword="{server_password}"', #Do NOT touch this, leave as is.
        'PublicIP="[^"]*"': f'PublicIP="{public_ip}"', #Do NOT touch this, leave as is.
        'PalEggDefaultHatchingTime=[0-9.]+': 'PalEggDefaultHatchingTime=72.000000', #3 days of hatching time.
        'BuildObjectDamageRate=[0-9.]+': 'BuildObjectDamageRate=1.000000',
        'BuildObjectDeteriorationDamageRate=[0-9.]+': 'BuildObjectDeteriorationDamageRate=1.000000',
        'DropItemMaxNum=[0-9]+': 'DropItemMaxNum=250',
        'DropItemMaxNum_UNKO=[0-9]+': 'DropItemMaxNum_UNKO=50',
        'BaseCampMaxNum=[0-9]+': 'BaseCampMaxNum=128',
        'BaseCampWorkerMaxNum=[0-9]+': 'BaseCampWorkerMaxNum=20',
        'ServerPlayerMaxNum=[0-9]+': 'ServerPlayerMaxNum=32',
        'bEnableNonLoginPenalty=[a-zA-Z]+': 'bEnableNonLoginPenalty=False',
        'bEnableFastTravel=[a-zA-Z]+': 'bEnableFastTravel=True',
        'bIsStartLocationSelectByMap=[a-zA-Z]+': 'bIsStartLocationSelectByMap=True',
        'bExistPlayerAfterLogout=[a-zA-Z]+': 'bExistPlayerAfterLogout=True',
        'bAutoResetGuildNoOnlinePlayers=[a-zA-Z]+': 'bAutoResetGuildNoOnlinePlayers=False',
        'AutoResetGuildTimeNoOnlinePlayers=[0-9.]+': 'AutoResetGuildTimeNoOnlinePlayers=336.000000', #14 days of inactivity will delete their bases/etc.
        'PalStaminaDecreaceRate=[0-9.]+': 'PalStaminaDecreaceRate=1.000000',
        'PalStomachDecreaceRate=[0-9.]+': 'PalStomachDecreaceRate=1.000000',
        'PlayerStaminaDecreaceRate=[0-9.]+': 'PlayerStaminaDecreaceRate=1.000000',
        'PlayerStomachDecreaceRate=[0-9.]+': 'PlayerStomachDecreaceRate=1.000000',
        'PalSpawnNumRate=[0-9.]+': 'PalSpawnNumRate=1.000000',
        'PalCaptureRate=[0-9.]+': 'PalCaptureRate=1.000000',
        'ExpRate=[0-9.]+': 'ExpRate=1.000000',
        'NightTimeSpeedRate=[0-9.]+': 'NightTimeSpeedRate=1.000000',
        'DayTimeSpeedRate=[0-9.]+': 'DayTimeSpeedRate=1.000000',
        'CollectionDropRate=[0-9.]+': 'CollectionDropRate=1.000000',
        'EnemyDropItemRate=[0-9.]+': 'EnemyDropItemRate=1.000000',
        'CollectionObjectHpRate=[0-9.]+': 'CollectionObjectHpRate=1.000000',
        'CollectionObjectRespawnSpeedRate=[0-9.]+': 'CollectionObjectRespawnSpeedRate=1.000000',
        'WorkSpeedRate=[0-9.]+': 'WorkSpeedRate=1.000000',
        'bEnablePlayerToPlayerDamage=[a-zA-Z]+': 'bEnablePlayerToPlayerDamage=False',
        'bEnableFriendlyFire=[a-zA-Z]+': 'bEnableFriendlyFire=False',
        'bEnableInvaderEnemy=[a-zA-Z]+': 'bEnableInvaderEnemy=False',
        'bActiveUNKO=[a-zA-Z]+': 'bActiveUNKO=False',
        'PalDamageRateAttack=[0-9.]+': 'PalDamageRateAttack=1.000000',
        'PalDamageRateDefense=[0-9.]+': 'PalDamageRateDefense=1.000000',
        'PlayerDamageRateAttack=[0-9.]+': 'PlayerDamageRateAttack=1.000000',
        'PlayerDamageRateDefense=[0-9.]+': 'PlayerDamageRateDefense=1.000000',
        'PlayerAutoHPRegeneRate=[0-9.]+': 'PlayerAutoHPRegeneRate=1.000000',
        'PlayerAutoHpRegeneRateInSleep=[0-9.]+': 'PlayerAutoHpRegeneRateInSleep=1.000000',
        'DropItemAliveMaxHours=[0-9.]+': 'DropItemAliveMaxHours=0.500000',
        'GuildPlayerMaxNum=[0-9]+': 'GuildPlayerMaxNum=20',
        'bIsMultiplay=[a-zA-Z]+': 'bIsMultiplay=False',
        'bIsPvP=[a-zA-Z]+': 'bIsPvP=False',
        'bCanPickupOtherGuildDeathPenaltyDrop=[a-zA-Z]+': 'bCanPickupOtherGuildDeathPenaltyDrop=False',
        'CoopPlayerMaxNum=[0-9]+': 'CoopPlayerMaxNum=4',
        'bUseAuth=[a-zA-Z]+': 'bUseAuth=True',
        'DeathPenalty=[0-9a-zA-Z]+': 'DeathPenalty=None',
        'bEnableDefenseOtherGuildPlayer=[a-zA-Z]+': 'bEnableDefenseOtherGuildPlayer=False',
        'bInvisibleOtherGuildBaseCampAreaFX=[a-zA-Z]+': 'bInvisibleOtherGuildBaseCampAreaFX=True',
        'AutoSaveSpan=[0-9.]+': 'AutoSaveSpan=60.000000',
        'BaseCampMaxNumInGuild=[0-9]+': 'BaseCampMaxNumInGuild=5',
        'SupplyDropSpan=[0-9]+': 'SupplyDropSpan=180',
        'AllowConnectPlatform=[a-zA-Z]+': 'AllowConnectPlatform=Steam', #Do NOT touch this, leave as is.
        'Difficulty=[a-zA-Z]+': 'Difficulty=None',
        'bEnableAimAssistPad=[a-zA-Z]+': 'bEnableAimAssistPad=True',
        'bEnableAimAssistKeyboard=[a-zA-Z]+': 'bEnableAimAssistKeyboard=False',
        'RandomizerType=[a-zA-Z]+': 'RandomizerType=None', #None, Region
        'RandomizerSeed="[a-zA-Z0-9]*"': 'RandomizerSeed="289BFC31469A6025DDB3"', #Randomly generated via solo world seed
        'bBuildAreaLimit=[a-zA-Z]+': 'bBuildAreaLimit=True',
        'bHardcore=[a-zA-Z]+': 'bHardcore=False',
        'bPalLost=[a-zA-Z]+': 'bPalLost=False',
        'ItemWeightRate=[0-9.]+': 'ItemWeightRate=1.000000',
        'MaxBuildingLimitNum=[0-9.]+': 'MaxBuildingLimitNum=0',
        'ServerReplicatePawnCullDistancee=[0-9.]+': 'ServerReplicatePawnCullDistance=5000',
        'EnablePredatorBossPal=[a-zA-Z]+': 'EnablePredatorBossPal=True',
        'Region="[a-zA-Z0-9]*"': 'Region="USA"',
        'LogFormatType=[a-zA-Z]+': 'LogFormatType=Json'
    }
    try:
        with open(config_file, 'r') as file:
            content = file.read()
        for search, replacement in replacements.items():
            content = re.sub(search, replacement, content)
        with open(config_file, 'w') as file:
            file.write(content)
        log("Palworld settings file update completed.")
    except Exception as e:
        log(f"Error updating Palworld settings file: {e}")        
def set_console_title(title):
    ctypes.windll.kernel32.SetConsoleTitleW(title)       
def clear_console():
    if platform.system() == 'Windows':
        os.system('cls')
    else:
        os.system('clear')        
for folder in [palserver_folder, log_folder, backup_folder]:
    os.makedirs(folder, exist_ok=True)    
def log(message):
    current_custom_time = get_custom_time()
    current_date = datetime.now().strftime("%Y-%m-%d")
    log_file_path = os.path.join(log_folder, f"{current_date}.txt")
    formatted_message = f"[{current_custom_time}] {message}"
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"{formatted_message}\n")
    print(formatted_message)
def get_custom_time():
    now = datetime.now()
    hour = now.strftime('%I').lstrip('0') 
    minute = now.strftime('%M')
    second = now.strftime('%S')
    ampm = now.strftime('%p')  
    return f"{hour}:{minute}:{second}{ampm}"    