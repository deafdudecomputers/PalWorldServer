from server_utils import *
from server_configurations import *
status_file_path = os.path.join(save_tools_folder, "fix_world_running.status")
lock_file_path = os.path.join(saved_folder, "clean_level_save.lock")
def retrieve_server_status():
    try:
        executable_name = os.path.basename(palserver_exe)
        process_id = get_process_id(executable_name)        
        if not process_id:
            log("Target process not running.")
            return        
        server_info = retrieve_info(f'http://{server_address}:{server_restapi_port}/v1/api/info', palserver_folder, 'server_info.json')
        if server_info:
            global server_version
            server_version = server_info.get('version', '')
            metrics_info = retrieve_info(f'http://{server_address}:{server_restapi_port}/v1/api/metrics', palserver_folder, 'metrics_info.json')
            if metrics_info:
                current_players = metrics_info.get('currentplayernum', '')
                server_fps = metrics_info.get('serverfps', '')
                uptime = check_uptime(executable_name) 
                memory_usage = check_memory_usage(palserver_exe) 
                log(f"[{server_version}][PID: {process_id}][FPS: {server_fps}][Players: {current_players}][{uptime}][MEM: {memory_usage}]")
            else:
                log("Metrics info retrieval failed.")            
            retrieve_server_player(server_address, server_restapi_port, admin_password, temp_file, online_file, log)
            save_server(admin_password, server_address, server_restapi_port)
            chat_logger(target_path)
            perform_backup(backup_folder, saved_folder, log, send_server_announcement)
            delete_old_files()
            check_memory_usage(palserver_exe) 
            check_uptime(palserver_exe)
            check_timer_scheduled()
            process_id = get_process_id(executable_name)
            if process_id:
                clean_level_save(server_file)
            else:
                log("Server is down, skipping clean_level_save.")
            execute_rcon_command("reloadcfg")
            check_update()
            force_restart()
        else:
            pass        
    except Exception as e:
        log(f"Error: Exception in retrieve_server_status. Exception: {e}")
def perform_backup(backup_folder, saved_folder, log, send_server_announcement):
    now = datetime.now()
    datestamp = now.strftime('%Y-%m-%d')
    hourstamp = now.strftime('%H')    
    temp_backup_folder = os.path.join(backup_folder, f"Backup_{datestamp}")
    os.makedirs(temp_backup_folder, exist_ok=True)    
    backup_file = os.path.join(temp_backup_folder, f"Backup_{hourstamp}.zip")    
    if not os.path.exists(backup_file):
        with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(saved_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.join(os.path.basename(saved_folder), os.path.relpath(file_path, start=saved_folder))
                    zipf.write(file_path, arcname=arcname)
        log("Server successfully backed up...")
        send_server_announcement("Server successfully backed up...")
def delete_old_files():
    try:
        now = time.time()
        for file in os.listdir(backup_folder):
            file_path = os.path.join(backup_folder, file)
            if os.stat(file_path).st_mtime < now - 30 * 86400:  # 30 days
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    log(f"Deleted old file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    log(f"Deleted old directory: {file_path}")
    except Exception as e:
        log(f"Error: Exception while deleting old files. Exception: {e}")       
def base64_auth_info():
    credentials = f"{username}:{admin_password}"
    return base64.b64encode(credentials.encode('ascii')).decode('ascii')
def retrieve_info(url, folder, file_name):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {base64_auth_info()}'
    }
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.status_code == 200:
            file_path = os.path.join(folder, file_name)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(response.json(), f, ensure_ascii=False)             
            with open(file_path, 'r', encoding='utf-8') as f: 
                data = json.load(f)                
            os.remove(file_path)
            return data
    except:
        pass
    return None   
def get_process_id(executable_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == executable_name:
            return proc.info['pid']
    return None    
def check_existing_instances(batch_title, palserver_exes, target_path, script_names):
    current_pid = os.getpid()
    server_pids = []
    script_pids = []
    def process_in_cmdline(cmdline):
        if cmdline is None:
            return False
        cmdline_str = ' '.join(cmdline).lower()
        return any(script_name.lower() in cmdline_str for script_name in script_names)
    def process_is_server(cmdline):
        if cmdline is None:
            return False
        cmdline_str = ' '.join(cmdline).lower()
        return any(exe.lower() in cmdline_str for exe in palserver_exes)
    for proc in psutil.process_iter(['pid', 'cmdline', 'name']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                if process_in_cmdline(cmdline):
                    script_pids.append(proc.info['pid'])
                elif process_is_server(cmdline):
                    if os.path.abspath(proc.cwd()) == os.path.abspath(target_path):
                        server_pids.append(proc.info['pid'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if len(script_pids) > 1:
        for pid in script_pids:
            if pid != current_pid:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
    for pid in server_pids:
        try:
            proc = psutil.Process(pid)
            proc.terminate()
            proc.wait()
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    if len(script_pids) > 1 or server_pids:
        sys.exit(1)        
def is_process_running(executable_path, target_path):
    executable_name = os.path.basename(executable_path).lower()
    def process_in_cmdline(cmdline):
        if cmdline is None:
            return False
        cmdline_str = ' '.join(cmdline).lower()
        return executable_name in cmdline_str
    def is_same_folder(process, path):
        try:
            cwd = process.cwd()
            return os.path.abspath(cwd) == os.path.abspath(path)
        except psutil.AccessDenied:
            return False
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmdline = proc.info['cmdline']
            if cmdline:
                if process_in_cmdline(cmdline):
                    if is_same_folder(proc, target_path):
                        return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False        
def retrieve_server_player(server_address, server_restapi_port, admin_password, temp_file, online_file, log):
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {base64.b64encode(f"admin:{admin_password}".encode()).decode()}'
    }
    url = f'http://{server_address}:{server_restapi_port}/v1/api/players'    
    try:
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        with open(temp_file, 'w', encoding='utf-8') as file:
            json.dump(response.json(), file, ensure_ascii=False, indent=4)
    except requests.HTTPError as http_err:
        log(f"HTTP error occurred: {http_err}")
        return
    except Exception as e:
        log(f"Error: Failed to retrieve players information. Exception: {e}")
        return    
    if not os.path.exists(temp_file):
        log("Error: Player list retrieval failed. File not created.")
        return    
    def extract_player_info(file_path):
        player_info = {}
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                for player in data.get('players', []):
                    name = player.get('name', '')
                    user_id = player.get('userId', '')
                    player_id = player.get('playerId', '')
                    level = player.get('level', '')
                    ip = player.get('ip', '')
                    player_info[name] = (user_id, player_id, level, ip)
        except (json.JSONDecodeError, KeyError) as e:
            log(f"Error: Failed to parse player list. Exception: {e}")
        return player_info
    temp_info = extract_player_info(temp_file)
    player_info = extract_player_info(online_file) if os.path.exists(online_file) else {}
    new_players = set(temp_info.keys()) - set(player_info.keys())
    left_players = set(player_info.keys()) - set(temp_info.keys())
    for player in new_players:
        user_id, player_id, level, ip = temp_info[player]
        message = f"{player} ({user_id}) ({player_id}) ({ip}) has joined the server."
        send_to_discord(message, discord_webhook_url)
        log(message)
        message = f"{player} has joined the server."
        send_server_announcement(message)
    for player in left_players:
        user_id, player_id, level, ip = player_info[player]
        message = f"{player} ({user_id}) ({player_id}) ({ip}) has left the server."
        send_to_discord(message, discord_webhook_url)
        log(message)
        message = f"{player} has left the server."
        send_server_announcement(message)
    os.replace(temp_file, online_file)
def send_server_announcement(message):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {base64.b64encode(f"admin:{admin_password}".encode()).decode()}'
    }    
    url = f'http://{server_address}:{server_restapi_port}/v1/api/announce'
    body = json.dumps({"message": message})    
    try:
        response = requests.post(url, headers=headers, data=body, timeout=3)
        response.raise_for_status()  
        if response.status_code == 200:
            log(f"Announcement sent: {message}")
        else:
            log(f"Error: Failed to send server announcement. Status code: {response.status_code}")
    except requests.HTTPError as http_err:
        log(f"HTTP error occurred: {http_err}")
    except Exception as e:
        log(f"Error: Failed to send server announcement. Exception: {e}")
def check_memory_usage(palserver_exe):
    executable_name = os.path.basename(palserver_exe)
    process_found = False
    memory_usage_mb = 0
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        if proc.info['name'] == executable_name:
            process_found = True
            memory_info = proc.info['memory_info']
            memory_usage_mb = memory_info.rss / (1024 * 1024) 
            break
    if process_found:
        memory_usage_gb = memory_usage_mb / 1024 
        return f"{memory_usage_mb:.2f} MB" if memory_usage_gb < 1 else f"{memory_usage_gb:.2f} GB"
    else:
        return "Process not found"
def check_uptime(palserver_exe):
    executable_name = os.path.basename(palserver_exe)
    process_id = get_process_id(executable_name)    
    if process_id:
        cmd_get_start_time = f'powershell "(Get-Process -Id {process_id} | Select-Object -ExpandProperty StartTime)"'
        result = subprocess.run(cmd_get_start_time, capture_output=True, text=True, shell=True)
        start_time_str = result.stdout.strip()        
        try:
            start_time = datetime.strptime(start_time_str, '%A, %B %d, %Y %I:%M:%S %p')
        except ValueError as e:
            log(f"Error parsing start time: {e}")
            return "Unknown"            
        current_time = datetime.now()
        uptime_seconds = int((current_time - start_time).total_seconds())
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60        
        if hours > 0:
            running_time = f"UPT: {hours}h:{minutes}m:{seconds}s"
        elif minutes > 0:
            running_time = f"UPT: {minutes}m:{seconds}s"
        else:
            running_time = f"UPT: {seconds}s"        
        return running_time
    else:
        return "Process not found"
def check_timer_scheduled():
    reboot_times_4_hours = ["00", "04", "08", "12", "16", "20"]
    reboot_times_3_hours = ["01", "05", "09", "13", "17", "21"]
    reboot_times_2_hours = ["02", "06", "10", "14", "18", "22"]
    reboot_times_1_hour = ["03", "07", "11", "15", "19", "23"]
    current_time = datetime.now()
    current_hour = current_time.strftime("%H")
    current_minute = current_time.strftime("%M")
    global last_checked_hour
    global restart_initiated
    if current_hour != last_checked_hour:
        restart_initiated = False
        last_checked_hour = current_hour
    if not restart_initiated:
        if current_hour in reboot_times_4_hours and current_minute == "00":
            log("Server is restarting now...")
            send_server_shutdown()
            restart_initiated = True
            reset_announcements()
            return
        if current_hour in reboot_times_3_hours and current_minute == "00":
            if not defined_announcement("announcement_3_hour"):
                send_server_announcement("Server restarting in 3 hours...")
                log("Server restarting in 3 hours...")
                set_announcement("announcement_3_hour")
        if current_hour in reboot_times_2_hours and current_minute == "00":
            if not defined_announcement("announcement_2_hour"):
                send_server_announcement("Server restarting in 2 hours...")
                log("Server restarting in 2 hours...")
                set_announcement("announcement_2_hour")
        if current_hour in reboot_times_1_hour:
            minute_announcements = {
                "55": "5 minutes",
                "56": "4 minutes",
                "57": "3 minutes",
                "58": "2 minutes",
                "59": "1 minute",
                "00": "1 hour"
            }
            if current_minute in minute_announcements:
                announcement_key = f"announcement_{minute_announcements[current_minute].replace(' ', '_')}"
                if not defined_announcement(announcement_key):
                    send_server_announcement(f"Server restarting in {minute_announcements[current_minute]}...")
                    log(f"Server restarting in {minute_announcements[current_minute]}...")
                    set_announcement(announcement_key)
def defined_announcement(announcement_key):
    return globals().get(announcement_key) is not None
def set_announcement(announcement_key):
    globals()[announcement_key] = True
def reset_announcements():
    global announcement_1_hour, announcement_2_hour, announcement_3_hour
    global announcement_5_minutes, announcement_4_minutes, announcement_3_minutes
    global announcement_2_minutes, announcement_1_minutes
    announcement_1_hour = None
    announcement_2_hour = None
    announcement_3_hour = None
    announcement_5_minutes = None
    announcement_4_minutes = None
    announcement_3_minutes = None
    announcement_2_minutes = None
    announcement_1_minutes = None
last_checked_hour = ""
restart_initiated = False
announcement_1_hour = None
announcement_2_hour = None
announcement_3_hour = None
announcement_5_minutes = None
announcement_4_minutes = None
announcement_3_minutes = None
announcement_2_minutes = None
announcement_1_minutes = None
save_performed_minute = ""
def save_server(admin_password, server_address, server_restapi_port):
    global save_performed_minute
    save_minutes = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]    
    current_time = datetime.now()
    current_save_minute = current_time.strftime("%M")
    if current_save_minute not in save_minutes:
        return    
    if save_performed_minute != current_save_minute:
        save_performed_minute = current_save_minute
    else:
        return
    url = f"http://{server_address}:{server_restapi_port}/v1/api/save"
    username = 'admin'
    password = admin_password
    base64_auth_info = base64.b64encode(f"{username}:{password}".encode('ascii')).decode('ascii')
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {base64_auth_info}'
    }
    try:
        response = requests.post(url, headers=headers, timeout=3)
        if response.ok:
            log("Server successfully saved.")
            send_server_announcement("Server successfully saved.")
        else:
            pass
    except requests.RequestException as e:
        pass
def force_restart():
    return
    log("Server is restarting now...")
    send_server_shutdown()
    #send_server_shutdown_old()
    restart_initiated = True
    reset_announcements()
    return
def send_server_shutdown():
    url = f"http://{server_address}:{server_restapi_port}/v1/api/shutdown"
    username = 'admin'
    password = admin_password
    base64_auth_info = base64.b64encode(f"{username}:{password}".encode('ascii')).decode('ascii')
    headers = {
        'Accept': 'application/json',
        'Authorization': f'Basic {base64_auth_info}'
    }
    waittime = 1
    shutdown_message = "Server will shut down now."
    data = {
        "waittime": waittime,
        "message": shutdown_message
    }    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=3)
        if response.ok:
            log("Server successfully shut down via REST API.")
            send_server_announcement("Server successfully shut down.")
        else:
            log(f"Server shutdown failed with status code: {response.status_code}")
    except requests.RequestException as e:
        log(f"Server shutdown request failed: {e}")    
def send_server_shutdown_old():
    for proc in psutil.process_iter(['pid', 'exe']):
        if proc.info['exe'] and target_path in proc.info['exe']:
            try:
                proc.terminate()
                proc.wait()
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    process_terminated = False
    for proc in psutil.process_iter(['pid', 'exe']):
        if proc.info['exe'] and target_path in proc.info['exe']:
            process_terminated = True
            break    
    if process_terminated:
        log("Server shutdown failed. Process still running.")
    else:
        log("Server successfully shut down.")    
def chat_logger(target_path):
    chatlog_file = os.path.join(target_path, "ChatLog.txt")
    last_line_file = os.path.join(target_path, "ChatLog_Last.txt")    
    if not os.path.exists(chatlog_file):
        with open(chatlog_file, 'w', encoding='utf-8') as f:
            f.write("0")    
    if not os.path.exists(last_line_file):
        with open(last_line_file, 'w', encoding='utf-8') as f:
            f.write("0")    
    with open(last_line_file, 'r', encoding='utf-8') as f:
        last_line = int(f.read().strip())    
    with open(chatlog_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()    
    for i, line in enumerate(lines[last_line:]):
        line = line.strip()
        last_line += 1
        send_to_discord(line, discord_webhook_url)
        log(f"{line}")    
    with open(last_line_file, 'w', encoding='utf-8') as f:
        f.write(str(last_line))      
def start_server():
    global server_query_port, server_port, server_address
    server_query_port = str(server_query_port)
    public_ip = ""
    server_port = str(server_port)
    cmd = [palserver_exe, 
           f"-QueryPort={server_query_port}", 
           f"-publicip={public_ip}", 
           f"-port={server_port}", 
           "-useperfthreads",
           "-UseMultithreadForDS"]
    if is_public:
        cmd.append("-publiclobby")
    try:
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        log(f"Server is starting up, please wait...")
    except Exception as e:
        log(f"Error starting server: {e}")      
def extract_buildid(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    try:
        buildid = data["data"][str(game_app_id)]["depots"]["branches"]["public"]["buildid"]
        return buildid
    except KeyError:
        log("Error: 'buildid' not found in the appinfo file.")
        return None
last_checked_minute = None
def check_update():
    global last_checked_minute    
    current_minute = time.localtime().tm_min
    if last_checked_minute == current_minute:
        return    
    last_checked_minute = current_minute
    appinfo_dir = os.path.join(palserver_folder, "steamapps")
    os.makedirs(appinfo_dir, exist_ok=True)
    appinfo_file = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}.acf")
    appinfo_file_new = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}_new.acf")
    url = f"https://api.steamcmd.net/v1/info/{game_app_id}"
    headers = {'Accept': 'application/json'}    
    try:
        response = requests.get(url, headers=headers, timeout=3)
        response.raise_for_status()
        data = response.json()
        status = data.get('status')
        if status and status.lower() == 'success':
            with open(appinfo_file_new, "w", encoding="utf-8") as file:
                json.dump(data, file)
        else:
            log(f"Error: Received unexpected status '{status}'.")
            return
    except requests.RequestException as e:
        log(f"Error: Failed to retrieve game app info. ({e})")
        return    
    old_buildid = extract_buildid(appinfo_file) if os.path.exists(appinfo_file) else None
    new_buildid = extract_buildid(appinfo_file_new)
    log(f"[Buildid] [Current: {old_buildid}] [New: {new_buildid}]")
    if old_buildid != new_buildid:
        log("Server update detected.")
        send_server_shutdown()    
    if os.path.exists(appinfo_file_new):
        os.remove(appinfo_file_new)
def update_server():
    if not os.path.exists(palserver_folder):
        os.makedirs(palserver_folder)
    log("Checking server update...")
    appinfo_dir = os.path.join(palserver_folder, "steamapps")
    os.makedirs(appinfo_dir, exist_ok=True)
    appinfo_file = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}.acf")
    appinfo_file_new = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}_new.acf")
    url = f"https://api.steamcmd.net/v1/info/{game_app_id}"
    headers = {'Accept': 'application/json'}
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            status = data.get('status')
            if status and status.lower() == 'success':
                with open(appinfo_file_new, "w", encoding="utf-8") as file:
                    json.dump(data, file)
                break
            else:
                log(f"Error: Received unexpected status '{status}'. Retrying in 1 second...")
                time.sleep(1)
        except requests.RequestException as e:
            log(f"Error: Failed to retrieve game app info. Retrying in 1 second... ({e})")
            time.sleep(1)
    old_buildid = extract_buildid(appinfo_file) if os.path.exists(appinfo_file) else None
    new_buildid = extract_buildid(appinfo_file_new)
    log(f"[Buildid] [Current: {old_buildid}] [New: {new_buildid}]")
    if old_buildid != new_buildid:
        log("Server update detected.")
        timestamp = time.strftime("%m-%d-%Y")
        update_dir = os.path.join(palserver_folder, "Server_Updates", f"{timestamp}-{new_buildid}")
        os.makedirs(update_dir, exist_ok=True)
        log("Server update downloading, please wait...")
        update_server_cmd = [
            steamcmd_path, "+force_install_dir", update_dir, "+login", "anonymous",
            "+app_update", str(game_app_id), "validate", "+quit"
        ]
        subprocess.run(update_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log("Server update successfully downloaded.")
        for item in os.listdir(update_dir):
            s = os.path.join(update_dir, item)
            d = os.path.join(palserver_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        log("Server files successfully updated.")
        os.replace(appinfo_file_new, appinfo_file)
    else:
        log("Server is already updated.")
    if os.path.exists(appinfo_file_new):
        os.remove(appinfo_file_new)
def update_server_forced():
    if not os.path.exists(palserver_folder):
        os.makedirs(palserver_folder)
    log("Checking server update...")
    log("Server update detected.")
    log("Server update downloading, please wait...")
    update_server_cmd = [
        steamcmd_path, "+force_install_dir", palserver_folder, "+login", "anonymous",
        "+app_update", str(game_app_id), "validate", "+quit"
    ]
    subprocess.run(update_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    log("Server update successfully downloaded.")
    log("Server files successfully updated.")
def move_depot_files():
    depot_download_folder = os.path.join(steamcmd_folder, "steamapps", "content", "app_2394010", "depot_2394011")    
    if os.path.exists(depot_download_folder):
        for item in os.listdir(depot_download_folder):
            s = os.path.join(depot_download_folder, item)
            d = os.path.join(palserver_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)    
    else:
        log("Depot files not found. Check the depot download path.")
def update_server_manifest(manifest):
    if not os.path.exists(palserver_folder):
        os.makedirs(palserver_folder)    
    log("Checking server update...")
    log("Server update detected.")
    log("Server update downloading, please wait...")    
    update_server_cmd = [
        steamcmd_path, "+login", "anonymous",
        "+download_depot", "2394010", "2394011", manifest,
        "+quit"
    ]
    subprocess.run(update_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)    
    move_depot_files()    
    log("Server update successfully downloaded.")
    log("Server files successfully updated.")
def send_to_discord(message, discord_webhook_url):
    message = message.replace("'", "''")
    payload = {'content': message}    
    response = requests.post(
        discord_webhook_url,
        headers={'Content-Type': 'application/json'},
        data=json.dumps(payload)
    )    
    if response.status_code != 204:
        print(f"Failed to send message: {response.status_code} - {response.text}")        
def playerslog_to_discord(discord_webhook_url):
    players_log = os.path.join(save_tools_folder, "players.log")
    if os.path.exists(players_log):
        try:
            with open(players_log, 'r', encoding='utf-8') as log_file:
                log_content = log_file.read()
        except UnicodeDecodeError:
            with open(players_log, 'r', encoding='latin-1') as log_file:
                log_content = log_file.read()
        max_length = 2000
        delay = 1 
        for i in range(0, len(log_content), max_length):
            chunk = log_content[i:i + max_length]
            send_to_discord(chunk, discord_webhook_url)
            time.sleep(delay)
    else:
        print("players.log not found.")        
def send_file_to_discord(discord_webhook_url, file_path, message_content=''):
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist.")
        return
    with open(file_path, 'rb') as file:
        files = {'file': (os.path.basename(file_path), file)}
        payload = {'content': message_content}
        response = requests.post(discord_webhook_url, files=files, data=payload)        
def delete_json_files():
    online_file = os.path.join(palserver_folder, "players_online.json")
    temp_file = os.path.join(palserver_folder, "temp_players.json")
    for file in [online_file, temp_file]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception as e:
                log("")                
def handle_fixed_files():
    players_log = os.path.join(save_tools_folder, "players.log")
    if os.path.exists(players_log):
        send_file_to_discord(discord_webhook_url, players_log, "Here is the latest players log file.")
        date_folder = datetime.now().strftime("%m.%d.%Y")
        hour_folder = datetime.now().strftime("%I %p") 
        server_players_folder = os.path.join(palserver_folder, "Server_Players", date_folder, hour_folder)
        os.makedirs(server_players_folder, exist_ok=True)
        log_filename = f"{datetime.now().strftime('%I.%M.%S%p')}_players.log"
        log_file_path = os.path.join(server_players_folder, log_filename)
        shutil.copy(players_log, log_file_path)
        pal_logger_folder = os.path.join(save_tools_folder, "Pal Logger")
        if os.path.exists(pal_logger_folder):
            zip_filename = f"{datetime.now().strftime('%I.%M.%S%p')}_Pal_Logger.zip"
            zip_file_path = os.path.join(server_players_folder, zip_filename)
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(pal_logger_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, pal_logger_folder))            
            send_file_to_discord(discord_webhook_url, zip_file_path, "Here is the latest zipped Pal Logger folder.")
        else:
            log("Pal Logger folder not found.")
    else:
        log("players.log not found.")        
def clean_level_save(server_file):
    current_time = time.localtime()
    minutes = current_time.tm_min
    if minutes % 10 != 0:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
        return    
    if os.path.exists(lock_file_path) or os.path.exists(status_file_path):
        return
    server_folder_name = get_server_folder_name(server_file, log)
    if not server_folder_name:
        log("DedicatedServerName not found!")
        return       
    level_save_search_path = os.path.join(saved_folder, "SaveGames", "0", server_folder_name, "Level.sav")
    players_folder_search_path = os.path.join(saved_folder, "SaveGames", "0", server_folder_name, "Players")    
    if not os.path.exists(level_save_search_path):
        log("Level.sav not found, skipping the task.")
        return
    try:
        with open(level_save_search_path, 'r+'):
            log("Level.sav is able to be used, processing with fix_world.cmd...")
    except IOError as e:
        log(f"Level.sav is currently in use or inaccessible: {e}")
        return
    fix_save = os.path.join(save_tools_folder, "fix_world.cmd")
    if not os.path.exists(fix_save):
        log("fix_world.cmd not found. Aborting...")
        return
    try:
        temp_level_save_path = os.path.join(save_tools_folder, "Level.sav")
        shutil.copy(level_save_search_path, temp_level_save_path)
        if not os.path.exists(temp_level_save_path):
            log("Failed to copy Level.sav to save_tools_folder. Aborting...")
            return
        log(f"Level.sav copied successfully to {temp_level_save_path}")
    except Exception as e:
        log(f"Error copying Level.sav: {e}")
        return
    try:
        players_folder_destination_path = os.path.join(save_tools_folder, "Players")
        if os.path.exists(players_folder_search_path):
            if os.path.exists(players_folder_destination_path):
                shutil.rmtree(players_folder_destination_path)
            shutil.copytree(players_folder_search_path, players_folder_destination_path)
            if not os.path.exists(players_folder_destination_path):
                log("Failed to copy the Players folder. Aborting...")
                return
            log(f"Players folder copied successfully to {players_folder_destination_path}")
        else:
            log("Players folder not found. Proceeding without Players data...")
    except Exception as e:
        log(f"Error copying Players folder: {e}")
        return
    try:
        with open(status_file_path, 'w') as status_file:
            status_file.write("Running")
        with open(lock_file_path, 'w') as lock_file:
            lock_file.write("Locked")
    except Exception as e:
        log(f"Error writing status or lock files: {e}")
        return
    def run_fix_world_cmd():
        log("Running fix_world.cmd, please wait...")
        process = None
        try:
            process = subprocess.Popen([fix_save, temp_level_save_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                process.communicate(timeout=300)
            except subprocess.TimeoutExpired:
                log("fix_world.cmd timed out. Terminating...")
                try:
                    process.kill()
                except Exception as kill_error:
                    log(f"Error terminating process: {kill_error}")
                try:
                    process.communicate()
                except Exception as comm_error:
                    log(f"Error communicating with process after kill: {comm_error}")
                log("fix_world.cmd terminated due to timeout.")
            else:
                log("Fix_world.cmd has completed the task...")
        except Exception as e:
            log(f"Error running fix_world.cmd: {e}")
        finally:
            if os.path.exists(status_file_path):
                os.remove(status_file_path)
            if os.path.exists(temp_level_save_path):
                os.remove(temp_level_save_path)
            if os.path.exists(players_folder_destination_path):
                shutil.rmtree(players_folder_destination_path)
            log("Temporary files cleaned up.")
            set_console_title(batch_title)
            handle_fixed_files()
    thread = threading.Thread(target=run_fix_world_cmd)
    thread.start()
def get_server_folder_name(server_file, log):
    if not os.path.exists(server_file):
        log("DedicatedServerName not found in the server file.")
        return None
    with open(server_file, 'r') as file:
        for line in file:
            if line.startswith("DedicatedServerName="):
                server_folder_name = line.strip().split("=", 1)[1]
                return server_folder_name
    log("DedicatedServerName not found in the server file.")
    return None
def execute_rcon_command(command):
    try:
        with MCRcon(server_address, admin_password, port=server_rcon_port) as mcr:
            response = mcr.command(command)
    except Exception as e:
        pass
def copy_config_section(default_file, target_file, start_marker):
    copy_lines = False
    with open(default_file, 'r', encoding='utf-8') as src, open(target_file, 'w', encoding='utf-8') as dest:
        for line in src:
            if line.startswith(start_marker):
                copy_lines = True
            if copy_lines:
                dest.write(line)
    log(f"Successfully copied from {default_file} to {target_file}")