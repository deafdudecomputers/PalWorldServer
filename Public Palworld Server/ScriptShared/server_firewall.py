import sys, os
script_shared_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'ScriptShared'))
sys.path.append(script_shared_path)
from server_configurations import *
from server_utils import *
def get_device_ip():
    return socket.gethostbyname(socket.gethostname())
def get_router_ip():
    result = subprocess.run(['powershell', '-Command', "(Get-NetRoute | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' -and $_.InterfaceAlias -ne 'Loopback Pseudo-Interface 1' } | Select-Object -First 1).NextHop"], capture_output=True, text=True)
    return result.stdout.strip()
def get_public_ip():
    response = requests.get('http://ipv4.icanhazip.com')
    return response.text.strip()
def check_firewall_rule(rule_name):
    result = subprocess.run(['netsh', 'advfirewall', 'firewall', 'show', 'rule', f'name={rule_name}'], capture_output=True, text=True)
    return result.returncode == 0
def add_firewall_rule(rule_name, protocol, port):
    subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', f'name={rule_name}', 'dir=in', 'action=allow', f'protocol={protocol}', f'localport={port}', 'profile=any'], capture_output=True, text=True)
    log(f"Firewall rule added for {rule_name}.")
def add_firewall_program_rule(rule_name, program_path):
    subprocess.run(['netsh', 'advfirewall', 'firewall', 'add', 'rule', f'name={rule_name}', 'dir=in', 'action=allow', f'program={program_path}', 'enable=yes', 'profile=any'], capture_output=True, text=True)
    log(f"Firewall rule added for {rule_name}.")
def update_firewall_rules(enable_custom_server_address, custom_server_address, server_query_port, server_port, server_rcon_port, server_restapi_port, server_name, palserver_exe_cmd, palserver_exe_original, palserver_exe_regular):
    log("Checking firewall...")    
    device_ip = get_device_ip()
    log(f"Device's IP is: {device_ip}")
    router_ip = get_router_ip()
    log(f"Router's IP is: {router_ip}")
    public_ip = get_public_ip()
    log(f"Public's IP is: {public_ip}")
    default_public_ip = public_ip
    if enable_custom_server_address:
        public_ip = custom_server_address
        log(f"Public's IP has been updated to: {public_ip}")
        check_cloudflare(default_public_ip)
    rules = [
        (f"Palworld Server Query Port {server_query_port}", "udp", server_query_port),
        (f"Palworld Server Port {server_port}", "udp", server_port),
        (f"Palworld Server RCON Port {server_rcon_port}", "udp", server_rcon_port),
        (f"Palworld Server REST API Port {server_restapi_port}", "tcp", server_restapi_port),
        (f"{server_name} PalServer-Win64-Shipping-Cmd", "program", palserver_exe_cmd),
        (f"{server_name} PalServer", "program", palserver_exe_original),
        (f"{server_name} PalServer-Win64-Shipping", "program", palserver_exe_regular)
    ]
    for rule_name, protocol, target in rules:
        if not check_firewall_rule(rule_name):
            if protocol == "program":
                add_firewall_program_rule(rule_name, target)
            else:
                add_firewall_rule(rule_name, protocol, target)
        else:
            log(f"Firewall rule {rule_name} already exists.")
    log("Firewall checks completed.")    
def check_cloudflare(public_ip):
    api_token = ""
    zone_id = ""
    record_id = ""
    record_name = ""
    log(f"Updating the DNS record {record_name}...")
    url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    data = {
        "type": "A",
        "name": record_name,
        "content": public_ip,
        "ttl": 1,
        "proxied": False
    }
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200 and response.json().get("success"):
            log(f"DNS record {record_name} updated successfully.")
        else:
            log(f"Failed to update DNS record {record_name}.")
    except Exception as e:
        log(f"Exception occurred: {e}")