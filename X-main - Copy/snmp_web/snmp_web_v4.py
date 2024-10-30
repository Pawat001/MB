from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import asyncio
from pysnmp.hlapi.v3arch.asyncio import get_cmd, set_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import socket

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# Dictionary to hold interface data
interface_data = {}

def is_valid_ip(ip):
    """Validate IP address format."""
    try:
        socket.inet_pton(socket.AF_INET, ip)
        return True
    except socket.error:
        return False

@app.route('/')
def index():
    return render_template('index_v4.html')

@socketio.on('get_snmp_info')
async def handle_get_snmp_info(data):
    print(f"Received data: {data}")  # Log entire data object
    ip = data.get('ip')
    ro = data.get('ro')
    rw = data.get('rw')
    
    if ip:
        print(f"Validating IP: {ip}")  # Log IP before validation
        if is_valid_ip(ip):
            await fetch_interfaces(ip, ro, rw)
        else:
            print("Invalid IP address format.")
    else:
        print("No IP address provided.")

@socketio.on('toggle_interface_status')
async def handle_toggle_interface_status(data):
    ip = data.get('ip')
    rw = data.get('rw')
    index = data.get('index')
    current_status = data.get('current_status')
    new_status = 2 if current_status == '1' else 1  # Toggle between 1 (Up) and 2 (Down)
    
    print(f"Received toggle request: IP: {ip}, RW: {rw}, Index: {index}, Current Status: {current_status}")

    if ip:
        await set_interface_status(ip, rw, index, new_status)
        await fetch_interfaces(ip, data.get('ro'), rw)  # Fetch updated status
    else:
        print("Invalid IP address received.")

async def fetch_interfaces(ip, ro, rw):
    global interface_data
    interface_data = {}
    index = 1

    # Fetch system info
    interface_data['sysName'] = await fetch_sys_info(ip, ro, '1.3.6.1.2.1.1.5.0')
    interface_data['sysDescr'] = await fetch_sys_info(ip, ro, '1.3.6.1.2.1.1.1.0')

    try:
        while True:
            interface_name = await fetch_interface_info(ip, ro, f'1.3.6.1.2.1.2.2.1.2.{index}')
            if not interface_name:
                break
            
            admin_status = await fetch_interface_info(ip, ro, f'1.3.6.1.2.1.2.2.1.7.{index}')
            interface_data[f'interface_{index}'] = {
                'name': interface_name,
                'admin_status': admin_status,
                'index': index
            }
            index += 1

    except Exception as e:
        print(f"Error fetching interfaces: {e}")
    
    emit('update_interface_data', interface_data)

async def fetch_sys_info(ip, community, oid):
    print(f"Fetching sys info from {ip} with OID {oid}")  # Logging
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData(community),
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    if errorIndication or errorStatus:
        print(f"Error fetching sys info: {errorIndication or errorStatus}")
    return str(varBinds[0][1]) if not errorIndication and not errorStatus else None

async def fetch_interface_info(ip, community, oid):
    print(f"Fetching interface info from {ip} with OID {oid}")  # Logging
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData(community),
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    if errorIndication or errorStatus:
        print(f"Error fetching interface info: {errorIndication or errorStatus}")
    return str(varBinds[0][1]) if not errorIndication and not errorStatus else None

async def set_interface_status(ip, community, index, status):
    print(f"Setting interface {index} status to {'Up' if status == 1 else 'Down'} for {ip}")  # Logging
    errorIndication, errorStatus, errorIndex, varBinds = await set_cmd(
        SnmpEngine(),
        CommunityData(community, mpModel=0),  # Ensure SNMP v2c by setting mpModel=0
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.7.{index}'), status)
    )
    if errorIndication or errorStatus:
        print(f"Error setting interface status: {errorIndication or errorStatus}")
    else:
        print(f"Interface {index} status set to {'Up' if status == 1 else 'Down'}.")

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)
