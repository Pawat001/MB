from flask import Flask, render_template, request, redirect, url_for, flash
import paramiko
import threading
import time
import io

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to a random secret key

# Global variables to hold SSH client and shell session
ssh_client = None
shell = None
output_buffer = io.StringIO()
interfaces = []  # To hold interface names
commandshrun = ["sh run", "show run", "do sh run", "do show run"]

def ssh_connect(ip, username, password):
    global ssh_client, shell, output_buffer, interfaces
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(ip, username=username, password=password)
        shell = ssh_client.invoke_shell()
        shell.send("terminal length 0\n")
        time.sleep(1)

        # Execute command to get interfaces
        shell.send("sh ip int b\n")
        time.sleep(1)  # Wait for command to execute

        while shell.recv_ready():
            output = shell.recv(1024).decode()
            output_buffer.write(output)
            parse_interfaces(output)

    except Exception as e:
        output_buffer.write(f"Connection Failed: {str(e)}\n")

def parse_interfaces(output):
    global interfaces
    lines = output.splitlines()
    for line in lines:
        # Here we assume that the interface names are the first word in each line.
        if line and not line.startswith('Interface'):  # Skip header line
            parts = line.split()
            if len(parts) >= 6:
                if parts[0] not in interfaces:
                        interfaces.append(parts[0])  # Add interface name to the list

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        ip = request.form['ip']
        username = request.form['username']
        password = request.form['password']
        # enable = request.form['enable']

        if not ip or not username or not password:
            flash('Please fill in all fields.')
            return redirect(url_for('index'))

        threading.Thread(target=ssh_connect, args=(ip, username, password)).start()
        interfaces = []
        return redirect(url_for('terminal'))

    return render_template('index.html')

@app.route('/terminal')
def terminal():
    global output_buffer
    return render_template('terminal.html', output=output_buffer.getvalue())

@app.route('/execute', methods=['POST'])
def execute():
    global shell, output_buffer
    command = request.form['command']
    print(type(command))
    if shell and (command not in commandshrun):
        shell.send(command + "\n")
        time.sleep(1)  # Wait for command to execute
        while shell.recv_ready():
            output = shell.recv(1024).decode()
            output_buffer.write(output)
    if shell and (command in commandshrun):
        shell.send(f"{command}\n")
        time.sleep(1)  # Wait for command to execute
        while shell.recv_ready():
            output = shell.recv(1024).decode()
            output_buffer.write(output)
        shell.send(f" \n")
        time.sleep(1)  # Wait for command to execute
        while shell.recv_ready():
            output = shell.recv(1024).decode()
            output_buffer.write(output)
    return redirect(url_for('terminal'))

@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        # Check for hostname submission
        if form_type == 'hostname':
            hostname = request.form['hostname']
            if not hostname:
                flash('Please enter a hostname.')
                return redirect(url_for('config'))
            if shell:
                shell.send(f"en\nconf t\nhostname {hostname}\nend\n")
                output_buffer.write(f"Configured hostname to {hostname}\n")
                return redirect(url_for('terminal'))

        # Check for IP address submission
        elif form_type == 'ip_address':
            ipv4 = request.form['ipv4']
            netmask = request.form['netmask']
            interface = request.form['interface']

            if not ipv4 or not netmask or interface == "Select Interface":
                flash('Please complete all fields.')
                return redirect(url_for('config'))

            if shell:
                shell.send(f"en\nconf t\ninterface {interface}\nip address {ipv4} {netmask}\nend\n")
                output_buffer.write(f"Configured {interface} with IP {ipv4}/{netmask}\n")
                return redirect(url_for('terminal'))

        # Check for shutdown submission
        elif form_type == 'shutdown':
            interface = request.form['interface']

            if interface == "Select Interface":
                flash('Please select an interface to shut down.')
                return redirect(url_for('config'))

            if shell:
                shell.send(f"en\nconf t\ninterface {interface}\nshutdown\nend\n")
                output_buffer.write(f"Shutdown applied to {interface}\n")
                return redirect(url_for('terminal'))

        # Check for no shutdown submission
        elif form_type == 'noshutdown':
            interface = request.form['interface']

            if interface == "Select Interface":
                flash('Please select an interface to enable.')
                return redirect(url_for('config'))

            if shell:
                shell.send(f"en\nconf t\ninterface {interface}\nno shutdown\nend\n")
                output_buffer.write(f"No Shutdown applied to {interface}\n")
                return redirect(url_for('terminal'))

    return render_template('config.html', interfaces=interfaces)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    global shell, output_buffer
    interface = request.form['interface']

    if shell and interface != "Select Interface":
        shell.send(f"en\nconf t\ninterface {interface}\nshutdown\nend\n")
        output_buffer.write(f"Shutdown applied to {interface}\n")
    return redirect(url_for('terminal'))

@app.route('/noshutdown', methods=['POST'])
def noshutdown():
    global shell, output_buffer
    interface = request.form['interface']

    if shell and interface != "Select Interface":
        shell.send(f"en\nconf t\ninterface {interface}\nno shutdown\nend\n")
        output_buffer.write(f"No Shutdown applied to {interface}\n")
    return redirect(url_for('terminal'))

@app.route('/clear_output', methods=['POST'])
def clear_output():
    global output_buffer
    output_buffer = io.StringIO()  # Reset the output buffer
    return redirect(url_for('terminal'))

if __name__ == '__main__':
    app.run(debug=True)
