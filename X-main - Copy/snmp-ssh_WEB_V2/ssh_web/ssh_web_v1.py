from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import paramiko
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

ssh_client = None
shell = None
connected = False

def ssh_connect(ip, username, password):
    global ssh_client, shell, connected
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username=username, password=password)

        shell = ssh_client.invoke_shell()
        connected = True

        socketio.emit('connection_status', {'status': 'Connected'})
        
        while connected:
            if shell.recv_ready():
                output = shell.recv(1024).decode()
                socketio.emit('terminal_output', {'output': output})
            time.sleep(0.1)
    except Exception as e:
        socketio.emit('connection_status', {'status': f'Connection Failed: {str(e)}'})

@app.route('/')
def home():
    return render_template('index_v1.html')

@app.route('/config', methods=['POST'])
def config():
    data = request.json
    hostname = data['hostname']
    enable = data['enable']

    if shell:
        shell.send(f"en\n{enable}\nconf t\nhostname {hostname}\n")
        return jsonify({'message': 'Hostname configured successfully'})
    return jsonify({'error': 'Not connected'}), 400

@app.route('/interface', methods=['POST'])
def interface():
    data = request.json
    ipv4 = data['ipv4']
    netmask = data['netmask']
    interface = data['interface']
    enable = data['enable']

    if shell and interface:
        command = f"en\n{enable}\nconf t\ninterface {interface}\nip address {ipv4} {netmask}\n"
        shell.send(command)
        return jsonify({'message': f'Configuration applied to {interface}'})
    return jsonify({'error': 'Incomplete Data'}), 400

@app.route('/shutdown', methods=['POST'])
def shutdown():
    interface = request.json['interface']
    enable = request.json['enable']

    if shell and interface:
        command = f"en\n{enable}\nconf t\ninterface {interface}\nshutdown\n"
        shell.send(command)
        return jsonify({'message': f'Shutdown applied to {interface}'})
    return jsonify({'error': 'Not connected'}), 400

@app.route('/noshutdown', methods=['POST'])
def noshutdown():
    interface = request.json['interface']
    enable = request.json['enable']

    if shell and interface:
        command = f"en\n{enable}\nconf t\ninterface {interface}\nno shutdown\n"
        shell.send(command)
        return jsonify({'message': f'No Shutdown applied to {interface}'})
    return jsonify({'error': 'Not connected'}), 400

@socketio.on('connect')
def handle_connect(data):
    ip = data['ip']
    username = data['username']
    password = data['password']
    threading.Thread(target=ssh_connect, args=(ip, username, password)).start()

@socketio.on('disconnect')
def handle_disconnect():
    global connected
    connected = False
    if ssh_client:
        ssh_client.close()
    socketio.emit('connection_status', {'status': 'Disconnected'})

if __name__ == "__main__":
    socketio.run(app, debug=True)
