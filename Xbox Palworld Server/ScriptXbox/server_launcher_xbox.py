import sys, os, time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ScriptShared.server_utils import *
from ScriptShared.server_firewall import *
from ScriptShared.server_installation_files import *
from ScriptShared.server_loop import *
from ScriptXbox.server_configurations import *
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
        update_server_manifest("2630252523734859869") #As of 9/16/2024, this is the latest Xbox version accessible to current clients. https://steamdb.info/depot/2394011/manifests/
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
def monitor_server():
    while True:
        try:
            if not is_process_running(palserver_exe, os.path.dirname(palserver_exe)):
                log("Server has stopped. Restarting the server...")
                setup_server()
            retrieve_server_status()
        except Exception as e:
            log(f"Error in loop: {e}")
def main():
    initialize()
    setup_server()
    monitor_server()
if __name__ == "__main__":
    main()