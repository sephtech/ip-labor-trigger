from tkinter import *
from pynput import mouse
import threading
import pythoncom
import tkinter as ttk
import wmi
import socket
import sys
import time

def set_network_options(device_name, network_adapter, set_network=True):

    switcher = {

        'fNIRS':                {'ip': u'192.168.1.2', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
        'Movisens EKG/EDA':     {'ip': u'192.168.1.3', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
        'Eyetracker':           {'ip': u'192.168.1.4', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
        'Motiontracker/EMG':    {'ip': u'192.168.1.5', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
        'Fahrsimulator':        {'ip': u'192.168.1.6', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'}
    }

    network_options = switcher.get(device_name)

    ip = network_options['ip']
    if text_ip.get("1.0",END) != '\n':
        ip = text_ip.get("1.0",END)

    port = 10001
    if text_port.get("1.0",END) != '\n':
        port = int(text_port.get("1.0",END))

    for nic in nics:
        if nic.ProductName == network_adapter:
            
            wmi_config = wmi.WMI().Win32_NetworkAdapterConfiguration(InterfaceIndex=nic.InterfaceIndex)

            if set_network:
                wmi_config[0].EnableStatic(IPAddress=[ip],SubnetMask=[network_options['netmask']])
                wmi_config[0].SetGateways(DefaultIPGateway=[network_options['gateway']])
                print(f"Changed network configuration of {network_adapter}\n\tto ip-{network_options['ip']}; netmask-{network_options['netmask']}; gateway-{network_options['gateway']}")
            else:
                exit_code = wmi_config[0].EnableDHCP()
                if exit_code == 0:
                    print(f"Changed network configuration of {network_adapter}\n\tto DHCP")
                else:
                    print(f"Change of network configuration to DHCP\n\tfailed because adapter is not connected.")
            
            break
    
    return (ip, port)

def set_firewall_rule(device_name, network_adapter, set_firewall=True):

    pass

def print_description(device_name):

    switcher = {

        'fNIRS': '''Start Oxysoft with administrator rights.
Start a measurement and change to the XXXX view.
Send a test trigger and check if it arrived.''',
        'Movisens EKG/EDA': '''Coming soon...''',
        'Eyetracker': '''Coming soon...''',
        'Motiontracker/EMG': '''Start CAPTIV with administrator rights.
Start a measurement and place the cursor above the trigger button.
Make sure that the CAPTIV window is in foreground.
Send a test trigger and check if the trigger value in CAPTIV increased.

WARNING: The highest trigger value is XXX. The following trigger will
reset the value and stop the measurement. Make sure you have enough
trigger values left!''',
        'Fahrsimulator': '''Start the driving simulator.
Send a test trigger and check if it arrived.
The triggers will be stored in this directory as csv files.
You have to restart this server for every participant.'''
    }

    print('\nDESCRIPTION:')
    print(switcher.get(device_name))
    print('\n')

def run_server():

    pythoncom.CoInitialize()
    device_name = tkvar_device.get()
    ip, port = set_network_options(device_name, tkvar_network.get())
    print_description(device_name)

    time.sleep(5)

    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = (ip, port)
    print(f'Server for {device_name} selected...')
    print('Starting up trigger server on %s on %s' % server_address)
    sock.bind(server_address)

    sock.listen(1)

    mouse_object = mouse.Controller()
    start_time = int(round(time.time() * 1000))

    while True:

        print('Waiting for connection')

        try:
            connection, client_address = sock.accept()

        finally:
            
            print('Socket closed...')
            break

        global stop_threads
        if stop_threads == True:
            break
        
        try:
            print('Connection from', client_address)
            received_message = ""
            
            while True:
                data = connection.recv(32)
                print('Received "%s"' % data)
                received_message = "".join((received_message, data.decode("utf-8")))
                
                if data:
                    print('Sending data back to the client')
                    connection.sendall(data)
                else:
                    print('No more data from', client_address)
                    break
                    
            trigger_parts = received_message.split("%SEP%")

            if device_name == 'fNIRS':
                trigger_fnirs(trigger_parts)
            elif device_name == 'Movisens EKG/EDA':
                trigger_movisens(trigger_parts)
            elif device_name == 'Eyetracker':
                trigger_eyetracker(trigger_parts)
            elif device_name == 'Motiontracker/EMG':
                trigger_motion(trigger_parts)
            elif device_name == 'Fahrsimulator':
                trigger_driving(trigger_parts, start_time)
                 
        finally:
            connection.close()

def trigger_fnirs(message):

    pass

def trigger_motion(message):

    mouse_object.click(mouse.Button.left, 1)

def trigger_movisens(message):

    pass

def trigger_driving(message, start_time):

    file = open("".join((str(start_time), ".csv")),"a")
    file.write("".join((str(int(round(time.time() * 1000))), ";", message[0], ";", message[1])))
    file.close()

def trigger_eyetracker(message):

    pass


nics = wmi.WMI().Win32_NetworkAdapter()
nic_names = []

for nic in nics:
    if nic.PhysicalAdapter != False:
        nic_names.append(nic.ProductName)

root = Tk()
root.title("Trigger Server")
root.minsize(300, 450)

# Add a grid
mainframe = Frame(root)
mainframe.grid(column=0,row=0, sticky=(N,W,E,S) )
mainframe.columnconfigure(0, weight = 1)
mainframe.rowconfigure(0, weight = 1)
mainframe.pack(pady = 50, padx = 50)

# Create the Tkinter variables for the dropdown
tkvar_device = StringVar(root)
tkvar_network = StringVar(root)
tkvar_advanced = IntVar(root)

# Dictionary with options
choices_devices = ('fNIRS', 'Movisens EKG/EDA', 'Fahrsimulator', 'Motiontracker/EMG')
choices_network = (nic_names)

tkvar_device.set(choices_devices[0]) # set the default option
tkvar_network.set(choices_network[0])

t = threading.Thread(name='non-daemon', target=run_server)

def button_start(*args):

    popupMenu['state'] = DISABLED
    popupMenu2['state'] = DISABLED
    check_btn['state'] = DISABLED

    text_ip["state"] = DISABLED
    text_ip["bg"] = "light gray"
    text_port["state"] = DISABLED
    text_port["bg"] = "light gray"

    btn_start['state'] = DISABLED
    btn_stop['state'] = NORMAL
    btn_reset['state'] = DISABLED

    label_popup1["fg"] = "gray"
    label_popup2["fg"] = "gray"
    label_ip["fg"] = "gray"
    label_port["fg"] = "gray"
    label_reset["fg"] = "gray"

    global stop_threads
    stop_threads = False
    t.start()

def button_stop(*args):
    
    global stop_threads
    global sock
    stop_threads = True
    sock.close()
    t.join()

    print('\nServer stopped...')

    popupMenu['state'] = NORMAL
    popupMenu2['state'] = NORMAL
    check_btn['state'] = NORMAL

    btn_start['state'] = NORMAL
    btn_stop['state'] = DISABLED
    btn_reset['state'] = NORMAL

    label_popup1["fg"] = "black"
    label_popup2["fg"] = "black"
    label_reset["fg"] = "black"

    change_advanced()

def button_reset(*args):
    set_network_options(tkvar_device.get(), tkvar_network.get(), False)

popupMenu = OptionMenu(mainframe, tkvar_device, *choices_devices)
label_popup1 = Label(mainframe, text="Choose the software running here")
label_popup1.grid(row = 1, column = 1)
popupMenu.grid(row = 2, column =1)

Label(mainframe, text="").grid(row = 3, column = 1)
popupMenu2 = OptionMenu(mainframe, tkvar_network, *choices_network)
label_popup2 = Label(mainframe, text="Choose the network adapter")
label_popup2.grid(row = 4, column = 1)
popupMenu2.grid(row = 5, column =1)

Label(mainframe, text="").grid(row = 6, column = 1)
check_btn = Checkbutton(mainframe, text = "Advanced Options", variable = tkvar_advanced, onvalue = 1, offvalue = 0, height=2, width = 20)
check_btn.grid(row = 7, column = 1)

label_ip = Label(mainframe, text="IP address:", width = 15, fg = "gray")
label_ip.grid(row = 8, column = 1)
text_ip = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
text_ip.grid(row = 9, column = 1)

label_port = Label(mainframe, text="Port:", width = 15, fg = "gray")
label_port.grid(row = 10, column = 1)
text_port = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
text_port.grid(row = 11, column = 1)

Label(mainframe, text="").grid(row = 12, column = 1)
btn_start = Button(mainframe, text = "Start", command = button_start)
btn_start.grid(row = 13, column = 1)
btn_stop = Button(mainframe, text = "Stop", state = DISABLED, command = button_stop)
btn_stop.grid(row = 14, column = 1)

Label(mainframe, text="").grid(row = 15, column = 1)
label_reset = Label(mainframe, text = "Reset network configuration for\nthe selected network adapter.\nOnly if adapter is connected!", height = 3)
label_reset.grid(row = 16, column = 1)
btn_reset = Button(mainframe, text = "Reset", command = button_reset)
btn_reset.grid(row = 17, column = 1)

def change_advanced(*args):
    if tkvar_advanced.get() == 0:
        text_ip["state"] = DISABLED
        text_ip["bg"] = "light gray"
        label_ip["fg"] = "gray"
        text_port["state"] = DISABLED
        text_port["bg"] = "light gray"
        label_port["fg"] = "gray"
    else:
        text_ip["state"] = NORMAL
        text_ip["bg"] = "white"
        label_ip["fg"] = "black"
        text_port["state"] = NORMAL
        text_port["bg"] = "white"
        label_port["fg"] = "black"

# link function to change dropdown
tkvar_advanced.trace('w', change_advanced)

import ctypes, sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if is_admin():
    
    root.mainloop()
else:
    # Re-run the program with admin rights
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)

