from server_utils import *
from server_configurations import *
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
            server_version = server_version.split('.')[0:3]
            server_version = '.'.join(server_version)
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
            chat_logger(target_path)
            perform_backup(backup_folder, saved_folder, log, send_server_announcement)
            delete_old_files()
            check_memory_usage(palserver_exe) 
            check_uptime(palserver_exe)
            check_timer_scheduled()
            process_id = get_process_id(executable_name)
            execute_rcon_command(f"reloadcfg")
            execute_rcon_command(f"save")
            #save_server()
            check_save_size()         
            check_update()
        else:
            pass        
    except Exception as e:
        log(f"Error: Exception in retrieve_server_status. Exception: {e}")
def check_save_size():
    save_last_minute = globals().get("save_last_minute")    
    server_folder_name = get_server_folder_name(server_file, log)
    level_save_path = os.path.join(saved_folder, "SaveGames", "0", server_folder_name, "Level.sav")    
    current_minute = datetime.now().minute
    if save_last_minute != current_minute:
        if os.path.exists(level_save_path):
            current_size = os.path.getsize(level_save_path)
            last_modified = datetime.fromtimestamp(os.path.getmtime(level_save_path)).strftime("%Y-%m-%d %H:%M:%S")
            last_size = globals().get("last_level_save_size")
            unchanged_attempts = globals().get("unchanged_attempts", 0)
            if last_size is not None and current_size == last_size:
                unchanged_attempts += 1
                log(f"Caution: Server save failed.")
                send_server_announcement(f"Caution: Server save failed.")
            else:
                unchanged_attempts = 0
                log("Server successfully saved.")
                send_server_announcement("Server successfully saved.")
            log(f"[Save][Current: {current_size}][Old: {last_size}][Checks: {unchanged_attempts}][Last Modified: {last_modified}]")
            globals()["last_level_save_size"] = current_size
            globals()["unchanged_attempts"] = unchanged_attempts
            if unchanged_attempts >= 3:
                log("Server is restarting due to a save failure.")
                send_server_announcement("Server is restarting due to a save failure.")
                globals()["last_level_save_size"] = None
                globals()["unchanged_attempts"] = 0
                send_server_shutdown()
        else:
            log(f"Level.sav file not found at: {level_save_path}")
        globals()["save_last_minute"] = current_minute
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
        retention_period = backup_days * 86400
        for file in os.listdir(backup_folder):
            file_path = os.path.join(backup_folder, file)
            if os.stat(file_path).st_mtime < now - retention_period:
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
    for proc in psutil.process_iter(['pid', 'name', 'exe']):
        if proc.info['name'] == executable_name and proc.info['exe'] and target_path in proc.info['exe']:
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
                    #send_server_shutdown()
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait()
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
    for pid in server_pids:
        try:
            #send_server_shutdown()
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
        log(message)
        message = f"{player} has joined the server."
        send_server_announcement(message)
    for player in left_players:
        user_id, player_id, level, ip = player_info[player]
        message = f"{player} ({user_id}) ({player_id}) ({ip}) has left the server."
        log(message)
        message = f"{player} has left the server."
        send_server_announcement(message)
    os.replace(temp_file, online_file)
def send_server_announcement(message):
    execute_rcon_command(f"pgbroadcast {message}")
    log(f"Announcement sent: {message}")
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
    if disable_reboots == 1:
        return
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
    return announcement_flags.get(announcement_key, False)
def set_announcement(announcement_key):
    announcement_flags[announcement_key] = True
def reset_announcements():
    global announcement_flags
    announcement_flags.clear()
last_checked_hour = ""
restart_initiated = False
announcement_flags = {}
save_performed_minute = ""
def save_server():
    global save_performed_minute
    save_minutes = ["00", "05", "10", "15", "20", "25", "30", "35", "40", "45", "50", "55"]
    current_save_minute = datetime.now().strftime("%M")    
    if current_save_minute not in save_minutes or save_performed_minute == current_save_minute:
        return    
    save_performed_minute = current_save_minute
    try:
        execute_rcon_command("save")
        log("Server successfully saved.")
        send_server_announcement("Server successfully saved.")
    except Exception as e:
        pass
def send_server_shutdown():
    send_server_shutdown_rcon()
    return
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
def send_server_shutdown_rcon():
    for proc in psutil.process_iter(['pid', 'exe']):
        if proc.info['exe'] and target_path in proc.info['exe']:
            try:
                shutdown_seconds = 1 
                shutdown_message = "Server will shutdown now."
                execute_rcon_command(f"shutdown {shutdown_seconds} {shutdown_message}")
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
        open(chatlog_file, 'w', encoding='utf-8').close()    
    if not os.path.exists(last_line_file):
        open(last_line_file, 'w', encoding='utf-8').close()    
    last_line = 0
    with open(last_line_file, 'r', encoding='utf-8') as f:
        last_line = int(f.read().strip() or 0)    
    with open(chatlog_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()    
    for i, line in enumerate(lines[last_line:]):
        line = line.strip()
        last_line += 1
        log(f"{line}")    
    with open(last_line_file, 'w', encoding='utf-8') as f:
        f.write(str(last_line))   
def start_server():
    global server_query_port, server_port, server_address
    server_query_port = str(server_query_port)
    public_ip = ""
    #public_ip = get_public_ip()
    server_port = str(server_port)
    cmd = [palserver_exe, 
           f"-QueryPort={server_query_port}", 
           f"-publicip={public_ip}", 
           f"-port={server_port}", 
           "-useperfthreads",
           "-NumberOfWorkerThreadsServer=7",
           "-UseMultithreadForDS"]
    if is_public:
        cmd.append("-publiclobby")
    try:
        subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        log(f"Server is starting up, please wait...")
    except Exception as e:
        log(f"Error starting server: {e}")      
last_checked_minute = None
def check_update():
    global last_checked_minute    
    current_minute = time.localtime().tm_min
    if last_checked_minute == current_minute:
        return    
    last_checked_minute = current_minute
    appinfo_dir = os.path.join(palserver_folder, "steamapps")
    os.makedirs(appinfo_dir, exist_ok=True)
    buildid_output_file = os.path.join(palserver_folder, "buildid_output.log")
    appinfo_file = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}.acf")
    steamcmd_cmd = [
        steamcmd_path, "+login", "anonymous", "+app_info_update", str(game_app_id),
        "+app_info_print", str(game_app_id), "+logoff", "+quit"
    ]
    with open(buildid_output_file, "w", encoding="utf-8") as output_file:
        try:
            subprocess.run(steamcmd_cmd, text=True, stdout=output_file, stderr=output_file, check=True)
        except subprocess.CalledProcessError as e:
            return
    buildid = extract_buildid_from_file(buildid_output_file)
    old_buildid = extract_buildid_from_file(appinfo_file) if os.path.exists(appinfo_file) else None
    log(f"[Buildid][Current: {old_buildid}][New: {buildid}]")
    if old_buildid != buildid:
        log("Server update detected.")
        send_server_shutdown()
    if os.path.exists(buildid_output_file):
        os.remove(buildid_output_file)
def extract_buildid_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            if '"buildid"' in line:
                return line.split('"')[3]
    return None
def update_server():
    if not os.path.exists(palserver_folder):
        os.makedirs(palserver_folder)
    log("Checking server update...")
    appinfo_dir = os.path.join(palserver_folder, "steamapps")
    os.makedirs(appinfo_dir, exist_ok=True)
    buildid_output_file = os.path.join(palserver_folder, "buildid_output.log")
    steamcmd_cmd = [
        steamcmd_path, "+login", "anonymous", "+app_info_update", "1",
        "+app_info_print", str(game_app_id), "+logoff", "+quit"
    ]
    with open(buildid_output_file, "w", encoding="utf-8") as output_file:
        result = subprocess.run(steamcmd_cmd, text=True, stdout=output_file, stderr=output_file)
    buildid = extract_buildid_from_file(buildid_output_file)
    if buildid is None:
        log("Server update detected.")
        timestamp = time.strftime("%m-%d-%Y")
        install_dir = os.path.join(palserver_folder, "Server_Install", f"{timestamp}")
        os.makedirs(install_dir, exist_ok=True)
        log("Installing the server, please wait...")
        install_server_cmd = [
            steamcmd_path, "+force_install_dir", install_dir, "+login", "anonymous",
            "+app_update", str(game_app_id), "validate", "+quit"
        ]
        subprocess.run(install_server_cmd, text=True, stdout=sys.stdout, stderr=sys.stderr)
        log("Server successfully installed.")
        for item in os.listdir(install_dir):
            s = os.path.join(install_dir, item)
            d = os.path.join(palserver_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        log("Server files successfully installed and copied.")
        return
    appinfo_file = os.path.join(appinfo_dir, f"appmanifest_{game_app_id}.acf")
    old_buildid = extract_buildid_from_file(appinfo_file) if os.path.exists(appinfo_file) else None
    log(f"[Buildid][Current: {old_buildid}][New: {buildid}]")
    if old_buildid != buildid:
        log("Server update detected.")
        timestamp = time.strftime("%m-%d-%Y")
        update_dir = os.path.join(palserver_folder, "Server_Updates", f"{timestamp}-{buildid}")
        os.makedirs(update_dir, exist_ok=True)
        log("Server update downloading, please wait...")
        update_server_cmd = [
            steamcmd_path, "+force_install_dir", update_dir, "+login", "anonymous",
            "+app_update", str(game_app_id), "validate", "+quit"
        ]
        subprocess.run(update_server_cmd, text=True, stdout=sys.stdout, stderr=sys.stderr)
        log("Server update successfully downloaded.")
        for item in os.listdir(update_dir):
            s = os.path.join(update_dir, item)
            d = os.path.join(palserver_folder, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        log("Server files successfully updated.")
    else:
        log("Server is already updated.")
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
    #subprocess.run(update_server_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(update_server_cmd, text=True, stdout=sys.stdout, stderr=sys.stderr) 
    move_depot_files()    
    log("Server update successfully downloaded.")
    log("Server files successfully updated.")              
def delete_json_files():
    online_file = os.path.join(palserver_folder, "players_online.json")
    temp_file = os.path.join(palserver_folder, "temp_players.json")
    for file in [online_file, temp_file]:
        if os.path.exists(file):
            try:
                os.remove(file)
            except Exception as e:
                log("")                     
def get_server_folder_name(server_file, log):
    if not os.path.exists(server_file):
        log("DedicatedServerName not found in the server file.")
        return None
    with open(server_file, 'r') as file:
        for line in file:
            if line.startswith("DedicatedServerName="):
                server_folder_name = line.strip().split("=", 1)[1]
                #log(f"Dedicated Server Name: {server_folder_name}")
                return server_folder_name
    log("DedicatedServerName not found in the server file.")
    return None
def execute_rcon_command(command, log_enabled=False):
    try:
        with MCRcon(server_address, admin_password, port=server_rcon_port) as mcr:
            response = mcr.command(command).strip()
            if log_enabled:
                log(f"Executing RCON command: {command}")
                log(f"Command executed successfully. Response: {response}")
            return response
    except Exception as e:
        if log_enabled:
            log(f"Error executing RCON command: {command}. Exception: {e}")
        return None
def copy_config_section(default_file, target_file, start_marker):
    copy_lines = False
    with open(default_file, 'r', encoding='utf-8') as src, open(target_file, 'w', encoding='utf-8') as dest:
        for line in src:
            if line.startswith(start_marker):
                copy_lines = True
            if copy_lines:
                dest.write(line)
    log(f"Successfully copied from {default_file} to {target_file}")