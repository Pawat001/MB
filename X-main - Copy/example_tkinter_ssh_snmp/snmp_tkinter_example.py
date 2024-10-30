import tkinter as tk
from tkinter import messagebox
import asyncio
from pysnmp.proto.api import v2c  # For SNMP types
import threading
from pysnmp.hlapi.v3arch.asyncio import get_cmd, set_cmd, SnmpEngine, CommunityData, UdpTransportTarget, ContextData, ObjectType, ObjectIdentity

class HomeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Home")

        # IP Entry
        self.ip_label = tk.Label(root, text="IP Address:")
        self.ip_label.grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = tk.Entry(root)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)

        # RO Entry
        self.ro_label = tk.Label(root, text="RO:")
        self.ro_label.grid(row=1, column=0, padx=5, pady=5)
        self.ro_entry = tk.Entry(root)
        self.ro_entry.grid(row=1, column=1, padx=5, pady=5)

        # RW Entry
        self.rw_label = tk.Label(root, text="RW:")
        self.rw_label.grid(row=2, column=0, padx=5, pady=5)
        self.rw_entry = tk.Entry(root)
        self.rw_entry.grid(row=2, column=1, padx=5, pady=5)

        # SNMP Button
        self.snmp_button = tk.Button(root, text="Open SNMP Interface", command=self.open_snmp)
        self.snmp_button.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

    def open_snmp(self):
        # Get user input
        ip = self.ip_entry.get()
        ro = self.ro_entry.get()
        rw = self.rw_entry.get()

        # Validate input
        if not ip or not ro or not rw:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return

        # Open SNMP window with user inputs
        snmp_window = SNMPApp(ip, ro, rw)
        snmp_window.run()

class SNMPApp:
    def __init__(self, ip, ro, rw):
        self.root = tk.Tk()
        self.root.title(f"SNMP Interfaces - {ip}")
        self.ip = ip
        self.ro = ro
        self.rw = rw

        self.interface_buttons = []
        self.asyncio_task = None

        # Create a scrollable frame
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Add labels for sysName and sysDescr
        self.sys_name_label = tk.Label(self.scrollable_frame, text="")
        self.sys_name_label.grid(row=0, column=0, padx=5, pady=5)

        self.sys_descr_label = tk.Label(self.scrollable_frame, text="")
        self.sys_descr_label.grid(row=1, column=0, padx=5, pady=5)

    def create_interface_row(self, index, name, admin_status):
        # Create a label for the interface name
        label = tk.Label(self.scrollable_frame, text=f"{name} (Interface {index})")
        label.grid(row=index + 2, column=0, padx=5, pady=5)  # Adjust row to start after sysName and sysDescr labels

        # Create a color button for the interface status (red = down, green = up)
        color = "green" if admin_status == 1 else "red"
        button = tk.Button(self.scrollable_frame, bg=color, width=10, command=lambda i=index: asyncio.run(self.toggle_interface_status(i)))
        button.grid(row=index + 2, column=1, padx=5, pady=5)

        self.interface_buttons.append(button)

    async def fetch_sys_info(self):
        # Get sysName (OID: 1.3.6.1.2.1.1.5.0)
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.ro),
            await UdpTransportTarget.create((self.ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.5.0'))  # sysName OID
        )
        if not errorIndication and not errorStatus:
            sys_name = str(varBinds[0][1])
            self.sys_name_label.config(text=f"System Name: {sys_name}")

        # Get sysDescr (OID: 1.3.6.1.2.1.1.1.0)
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.ro),
            await UdpTransportTarget.create((self.ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))  # sysDescr OID
        )
        if not errorIndication and not errorStatus:
            sys_descr = str(varBinds[0][1])
            self.sys_descr_label.config(text=f"System Description: {sys_descr}")

    async def fetch_interfaces(self):
        # Fetch sysName and sysDescr first
        await self.fetch_sys_info()

        # Async SNMP GET request for each interface
        index = 1
        try:
            while True:
                # Get interface description
                errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                    SnmpEngine(),
                    CommunityData(self.ro),
                    await UdpTransportTarget.create((self.ip, 161)),
                    ContextData(),
                    ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.2.{index}'))  # Interface description OID
                )

                if errorIndication or errorStatus:
                    break

                interface_name = str(varBinds[0][1])

                # Get admin status
                errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
                    SnmpEngine(),
                    CommunityData(self.ro),
                    await UdpTransportTarget.create((self.ip, 161)),
                    ContextData(),
                    ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.7.{index}'))  # Admin status OID
                )

                admin_status = int(varBinds[0][1])
                self.create_interface_row(index, interface_name, admin_status)

                index += 1
        except Exception as e:
            print(f"Error fetching interfaces: {e}")

    async def toggle_interface_status(self, index):
        # Get current admin status
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.ro),
            await UdpTransportTarget.create((self.ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.7.{index}'))  # Admin status OID
        )

        if errorIndication or errorStatus:
            print(f"Error: {errorIndication or errorStatus}")
            return

        current_status = int(varBinds[0][1])
        new_status = 2 if current_status == 1 else 1  # Toggle between up (1) and down (2)

        # Set new admin status
        errorIndication, errorStatus, errorIndex, varBinds = await set_cmd(
            SnmpEngine(),
            CommunityData(self.rw),
            await UdpTransportTarget.create((self.ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.7.{index}'), v2c.Integer(new_status))  # Update admin status OID
        )

        if errorIndication or errorStatus:
            print(f"Error setting new status: {errorIndication or errorStatus}")
            return

        # Check if the status actually changed
        errorIndication, errorStatus, errorIndex, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData(self.ro),
            await UdpTransportTarget.create((self.ip, 161)),
            ContextData(),
            ObjectType(ObjectIdentity(f'1.3.6.1.2.1.2.2.1.7.{index}'))  # Admin status OID
        )

        if not errorIndication and not errorStatus:
            updated_status = int(varBinds[0][1])
            self.interface_buttons[index - 1].config(bg="green" if updated_status == 1 else "red")

    def run(self):
        self.asyncio_task = threading.Thread(target=lambda: asyncio.run(self.fetch_interfaces()))
        self.asyncio_task.start()
        self.root.mainloop()

    def on_closing(self):
        if self.asyncio_task:
            self.asyncio_task.join()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = HomeApp(root)
    root.mainloop()
