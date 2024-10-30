from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import asyncio
from pysnmp.proto.api import v2c
from pysnmp.hlapi.v3arch.asyncio import get_cmd, set_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

# A dictionary to hold the interface data
interface_data = {}

@app.route('/')
def index():
    return render_template('index_v2.html')

@socketio.on('get_snmp_info')
def handle_get_snmp_info(data):
    ip = data['ip']
    ro = data['ro']
    rw = data['rw']
    
    # Start the asynchronous function to fetch SNMP data
    asyncio.run(fetch_interfaces(ip, ro, rw))

async def fetch_interfaces(ip, ro, rw):
    global interface_data
    interface_data = {}  # Reset data for new request
    index = 1
    
    # Fetch sysName and sysDescr first
    sys_name = await fetch_sys_info(ip, ro, '1.3.6.1.2.1.1.5.0')
    sys_descr = await fetch_sys_info(ip, ro, '1.3.6.1.2.1.1.1.0')

    interface_data['sysName'] = sys_name
    interface_data['sysDescr'] = sys_descr
    
    try:
        while True:
            # Get interface description
            interface_name = await fetch_interface_info(ip, ro, f'1.3.6.1.2.1.2.2.1.2.{index}')
            if not interface_name:
                break
            
            # Get admin status
            admin_status = await fetch_interface_info(ip, ro, f'1.3.6.1.2.1.2.2.1.7.{index}')
            interface_data[f'interface_{index}'] = {
                'name': interface_name,
                'admin_status': admin_status
            }
            index += 1

    except Exception as e:
        print(f"Error fetching interfaces: {e}")
    
    emit('update_interface_data', interface_data)

async def fetch_sys_info(ip, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData(community),
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    if not errorIndication and not errorStatus:
        return str(varBinds[0][1])
    return None

async def fetch_interface_info(ip, community, oid):
    errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
        SnmpEngine(),
        CommunityData(community),
        await UdpTransportTarget.create((ip, 161)),
        ContextData(),
        ObjectType(ObjectIdentity(oid))
    )
    if not errorIndication and not errorStatus:
        return str(varBinds[0][1])
    return None

if __name__ == '__main__':
    socketio.run(app, debug=True)
