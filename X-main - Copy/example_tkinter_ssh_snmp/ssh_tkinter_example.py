import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
import paramiko
import threading
import time

class HomeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Home")

        # IP Entry
        self.ip_label = tk.Label(root, text="IP Address:")
        self.ip_label.grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        # Username Entry
        self.username_label = tk.Label(root, text="Username:")
        self.username_label.grid(row=1, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(root)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        # Password Entry
        self.password_label = tk.Label(root, text="Password:")
        self.password_label.grid(row=2, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(root, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)

        # Enable Entry
        self.enable_label = tk.Label(root, text="Enable:")
        self.enable_label.grid(row=3, column=0, padx=5, pady=5)
        self.enable_entry = tk.Entry(root, show="*")
        self.enable_entry.grid(row=3, column=1, padx=5, pady=5)

        # Config Button
        self.config_button = tk.Button(root, text="Config", command=self.open_config)
        self.config_button.grid(row=4, column=0, padx=5, pady=5)

        # Terminal Button
        self.terminal_button = tk.Button(root, text="Terminal", command=self.open_terminal)
        self.terminal_button.grid(row=4, column=1, padx=5, pady=5)

    def open_terminal(self):
        # Get user input
        ip = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        # enable = self.enable_entry.get()

        # Validate input
        if not ip or not username or not password:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        # Open terminal window with user inputs
        terminal_window = TerminalApp(ip, username, password)
        terminal_window.run()  # Start the terminal application

    def open_config(self):
        # Get user input
        ip = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        enable = self.enable_entry.get()

        # Validate input
        if not ip or not username or not password:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        # Open config window with user inputs
        config_window = ConfigApp(ip, username, password, enable)
        config_window.run()  # Start the config application

class TerminalApp:
    def __init__(self, ip, username, password):
        self.root = tk.Tk()
        self.root.title("Terminal")
        self.ip = ip
        self.username = username
        self.password = password

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Terminal Output (Scrolled Text)
        self.output_text = scrolledtext.ScrolledText(self.root, width=80, height=20)
        self.output_text.grid(row=0, column=0, columnspan=3, padx=5, pady=5)
        self.output_text.config(state=tk.DISABLED)

        # Command Entry
        self.command_entry = tk.Entry(self.root, width=80)
        self.command_entry.grid(row=1, column=0, padx=5, pady=5)
        self.command_entry.bind("<Return>", self.execute_command)

        # Execute Button
        self.execute_button = tk.Button(self.root, text="Execute", command=self.execute_command)
        self.execute_button.grid(row=1, column=1, padx=5, pady=5)

        # Clear Button
        self.clear_button = tk.Button(self.root, text="Clear", command=self.clear_output)
        self.clear_button.grid(row=1, column=2, padx=5, pady=5)

        # SSH client and shell session
        self.ssh_client = None
        self.shell = None
        self.prompt = ""  # To store the last command prompt

        # Start SSH connection
        threading.Thread(target=self.ssh_connect).start()

    def ssh_connect(self):
        try:
            # Create SSH client and connect
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.ip, username=self.username, password=self.password)

            # Start an interactive shell session
            self.shell = self.ssh_client.invoke_shell()
            self.display_output(f"Connected to {self.ip}.\n")

            # Set terminal length to 0 to disable pagination
            self.shell.send("terminal length 0\n")
            time.sleep(1)  # Give it some time to process the command

            # Keep reading and displaying data from SSH shell
            while True:
                if self.shell.recv_ready():
                    output = self.shell.recv(1024).decode()
                    self.display_output(output)

                # Add a small delay to prevent high CPU usage
                time.sleep(0.1)

        except Exception as e:
            messagebox.showerror("Connection Failed", f"Error: {str(e)}")

    def execute_command(self, event=None):
        command = self.command_entry.get()
        if self.shell and command:
            # Send command to the SSH shell
            self.shell.send(command + "\n")
            self.command_entry.delete(0, tk.END)  # Clear command entry
        else:
            messagebox.showerror("Not Connected", "No active SSH connection or command is empty.")

    def clear_output(self):
        # Clear the output text area while keeping the last line (the prompt)
        self.output_text.config(state=tk.NORMAL)
        lines = self.output_text.get(1.0, tk.END).splitlines()
        # Keep the last line (the prompt) if it exists
        if len(lines) > 1:
            self.output_text.delete(1.0, tk.END)  # Clear all text
            self.output_text.insert(tk.END, lines[-1])  # Insert the last line (the prompt)
        else:
            self.output_text.delete(1.0, tk.END)  # Clear all text if no lines
        self.output_text.config(state=tk.DISABLED)

    def display_output(self, output):
        # Enable text widget to write, then disable after writing
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, output)
        self.output_text.config(state=tk.DISABLED)
        self.output_text.yview(tk.END)  # Scroll to the bottom
        # Update the prompt variable
        self.prompt = output.splitlines()[-1] if output.splitlines() else ""

    def on_closing(self):
        # Cleanly close the SSH connection if it's open
        if self.ssh_client:
            self.ssh_client.close()
        self.root.destroy()  # Close the application

    def run(self):
        self.root.mainloop()

class ConfigApp:
    def __init__(self, ip, username, password,enable):
        self.root = tk.Tk()
        self.root.title("Config")
        self.ip = ip
        self.username = username
        self.password = password
        self.enable = enable

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Hostname Label (left side of hostname entry)
        self.hostname_label = tk.Label(self.root, text="Hostname:")
        self.hostname_label.grid(row=0, column=0, padx=5, pady=5, sticky='e')

        # Hostname Entry
        self.hostname_entry = tk.Entry(self.root, width=80)
        self.hostname_entry.grid(row=0, column=1, padx=5, pady=5)
        self.hostname_entry.bind("<Return>", self.hostname_command)

        # Execute Button for Hostname
        self.hostname_button = tk.Button(self.root, text="Submit Hostname", command=self.hostname_command)
        self.hostname_button.grid(row=0, column=2, padx=5, pady=5)

        # Interface Dropdown Label
        self.interface_label = tk.Label(self.root, text="Select Interface:")
        self.interface_label.grid(row=1, column=0, padx=5, pady=5, sticky='e')

        # Placeholder for dropdown interfaces (will be populated after SSH connection)
        self.interfaces = tk.StringVar(self.root)
        self.interfaces.set("Select Interface")

        # Dropdown Menu for interfaces
        self.interface_dropdown = tk.OptionMenu(self.root, self.interfaces, "Loading...")
        self.interface_dropdown.grid(row=1, column=1, padx=5, pady=5)

        # IPv4 Label
        self.ipv4_label = tk.Label(self.root, text="IPv4:")
        self.ipv4_label.grid(row=2, column=0, padx=5, pady=5, sticky='e')

        # IPv4 Entry
        self.ipv4_entry = tk.Entry(self.root, width=80)
        self.ipv4_entry.grid(row=2, column=1, padx=5, pady=5)

        # Netmask Label
        self.netmask_label = tk.Label(self.root, text="Netmask:")
        self.netmask_label.grid(row=3, column=0, padx=5, pady=5, sticky='e')

        # Netmask Entry
        self.netmask_entry = tk.Entry(self.root, width=80)
        self.netmask_entry.grid(row=3, column=1, padx=5, pady=5)

        # Shared Submit Button for Interface, IPv4, and Netmask
        self.interface_button = tk.Button(self.root, text="Submit Interface Config", command=self.interface_command)
        self.interface_button.grid(row=3, column=2, padx=5, pady=5)

        self.shutdown_button = tk.Button(self.root, text="Shutdown port", command=self.shutdown_command)
        self.shutdown_button.grid(row=4, column=0, padx=5, pady=5)

        self.noshutdown_button = tk.Button(self.root, text="No Shutdown port", command=self.noshutdown_command)
        self.noshutdown_button.grid(row=4, column=1, padx=5, pady=5)

        # SSH client and shell session
        self.ssh_client = None
        self.shell = None
        self.prompt = ""  # To store the last command prompt

        # Start SSH connection
        threading.Thread(target=self.ssh_connect).start()

    def ssh_connect(self):
        try:
            # Create SSH client and connect
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh_client.connect(self.ip, username=self.username, password=self.password)

            # Start an interactive shell session
            self.shell = self.ssh_client.invoke_shell()

            # Send commands to retrieve interface list
            self.shell.send("terminal length 0\nshow ip int brief\n")
            time.sleep(1)

            # Capture the output and process interfaces
            output = self.shell.recv(65535).decode()
            lines = output.splitlines()

            # Filter out interfaces based on common prefixes (Fast, Gigabit, Serial, etc.)
            interfaces = [line.split()[0] for line in lines if line.startswith(('Fast', 'Giga', 'Serial'))]
            port = [line.split()[len(line.split())-1] for line in lines if line.startswith(('Fast', 'Giga', 'Serial'))]
            print(interfaces,port)
            # Update dropdown menu with the list of interfaces
            menu = self.interface_dropdown["menu"]
            menu.delete(0, "end")
            for interface in interfaces:
                menu.add_command(label=interface, command=lambda value=interface: self.interfaces.set(value))

            # Set the initial value
            self.interfaces.set("Select Interface")

        except Exception as e:
            messagebox.showerror("Connection Failed", f"Error: {str(e)}")

    def hostname_command(self, event=None):
        """Send the hostname command to the SSH shell"""
        command = self.hostname_entry.get()
        enable = self.enable
        if self.shell and command:
            self.shell.send(f"en\n{enable}\nconf t\nhostname {command}\n")
            self.hostname_entry.delete(0, tk.END)
            messagebox.showinfo("Success", "Hostname configured")

    def interface_command(self):
        """Send the interface configuration (interface, IPv4, netmask) to the SSH shell"""
        ipv4 = self.ipv4_entry.get()
        netmask = self.netmask_entry.get()
        interface = self.interfaces.get()
        enable = self.enable

        if self.shell and ipv4 and netmask and interface != "Select Interface":
            # Send commands to configure the interface
            command = f"en\n{enable}\nconf t\ninterface {interface}\nip address {ipv4} {netmask}\n"
            self.shell.send(command)
            self.ipv4_entry.delete(0, tk.END)
            self.netmask_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Configuration applied to {interface}")
        else:
            messagebox.showerror("Incomplete Data", "Please select an interface and provide both IPv4 and Netmask values.")

    def shutdown_command(self):
        """Send the interface configuration (interface, IPv4, netmask) to the SSH shell"""
        interface = self.interfaces.get()
        enable = self.enable

        if self.shell and interface != "Select Interface":
            # Send commands to configure the interface
            command = f"en\n{enable}\nconf t\ninterface {interface}\nshutdown\n"
            self.shell.send(command)
            self.ipv4_entry.delete(0, tk.END)
            self.netmask_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"Shutdown applied to {interface}")
        else:
            messagebox.showerror("Incomplete Data")

    def noshutdown_command(self):
        """Send the interface configuration (interface, IPv4, netmask) to the SSH shell"""
        interface = self.interfaces.get()
        enable = self.enable

        if self.shell and interface != "Select Interface":
            # Send commands to configure the interface
            command = f"en\n{enable}\nconf t\ninterface {interface}\nno shutdown\n"
            self.shell.send(command)
            self.ipv4_entry.delete(0, tk.END)
            self.netmask_entry.delete(0, tk.END)
            messagebox.showinfo("Success", f"No Shutdown applied to {interface}")
        else:
            messagebox.showerror("Incomplete Data")

    def on_closing(self):
        """Cleanly close the SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = HomeApp(root)
    root.mainloop()