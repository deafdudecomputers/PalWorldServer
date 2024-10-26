import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ScriptShared.server_utils import *
from ScriptShared.server_firewall import *
from ScriptShared.server_installation_files import *
from ScriptShared.server_loop import *
from ScriptPublic.server_configurations import *
def get_script_path():
    return os.path.abspath(__file__)
def get_script_name():
    return os.path.basename(get_script_path())
def initialize():
    set_console_title(batch_title)
    clear_console()
    if os.path.exists(status_file_path):
        os.remove(status_file_path)
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)
def setup_server():
    log(f"Script names: {[get_script_name()]}")
    check_existing_instances(batch_title, palserver_exes, target_path, [get_script_name()])
    if is_process_running(palserver_exe, os.path.dirname(palserver_exe)):
        log("Server is running. Proceeding with cleanup.")
        delete_zipped_files(palserver_folder, log)
    else:
        log("Server is not running. Performing setup.")
        log(personalize_message)
        check_powershell()
        download_and_extract_files(server_files_url, palserver_folder)
        extract_steamcmd()
        update_server()
        #update_server_manifest("2890553081164318345") #As of 9/30/2024, this is the latest Xbox version accessible to current clients. https://steamdb.info/depot/2394011/manifests/
        #update_server_forced()
        install_mods()
        install_server_tweaks()
        copy_config_section(default_config_file, config_file, '[/Script/Pal.PalGameWorldSettings]')
        check_reduce_memory()
        check_and_install_palguard(palserver_folder, target_path, palguard_enabled, log)
        update_palguard_json()
        check_and_install_save_tools(palserver_folder, save_tools_folder, log)
        public_ip = get_public_ip()
        update_firewall_rules(
            enable_custom_server_address, custom_server_address, server_query_port, server_port,
            server_rcon_port, server_restapi_port, server_name, palserver_exe_cmd,
            palserver_exe_original, palserver_exe_regular
        )
        update_palworldsettings_file(
            config_file, server_restapi_port, server_rcon_port, server_port, admin_password,
            config_server_name, config_server_desc, server_password, public_ip
        )
        update_engine_file()
        delete_zipped_files(palserver_folder, log)
        delete_json_files()
        start_server()
        time.sleep(loop_time)
heartbeat_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "monitor_heartbeat.txt")
monitor_thread = None
monitor_stop_event = threading.Event() 
def update_heartbeat():
    with open(heartbeat_file, "w") as f:
        f.write(str(time.time()))
def monitor_server():
    while True:
        if monitor_stop_event.is_set():
            log("Monitor server stopping...")
            break
        try:
            update_heartbeat()
            if not is_process_running(palserver_exe, os.path.dirname(palserver_exe)):
                log("Server has stopped. Restarting the server...")
                setup_server()
            retrieve_server_status()
        except Exception as e:
            log(f"Error in loop: {e}")
def watchdog():
    global monitor_thread
    while True:
        try:
            if os.path.exists(heartbeat_file):
                with open(heartbeat_file, "r") as f:
                    last_heartbeat = float(f.read())
                if time.time() - last_heartbeat > 30:
                    log("Monitor server unresponsive. Restarting monitor...")
                    if monitor_thread and monitor_thread.is_alive():
                        log("Shutting down old monitor thread...")
                        monitor_stop_event.set()
                        monitor_thread.join()
                        monitor_stop_event.clear()
                    monitor_thread = threading.Thread(target=monitor_server)
                    monitor_thread.start()
            else:
                log("Heartbeat file missing. Starting monitor server...")
                if monitor_thread and monitor_thread.is_alive():
                    monitor_stop_event.set()
                    monitor_thread.join()
                    monitor_stop_event.clear()
                monitor_thread = threading.Thread(target=monitor_server)
                monitor_thread.start()
        except Exception as e:
            log(f"Error in watchdog: {e}")
        time.sleep(10)
def main():
    initialize()
    setup_server()
    watchdog()
if __name__ == "__main__":
    main()