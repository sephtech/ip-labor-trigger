from tkinter import *
from pynput import mouse
from subprocess import DEVNULL
import subprocess
import threading
import pythoncom
import tkinter as ttk
import logging
import wmi
import ctypes
import socket
import sys
import time

class HFU_Trigger_Server():
    '''
    Program for receiving trigger data sent over TCP/IP.
    Target device selectable with GUI.
    Network configurations are automatet.
    '''

    def __init__(self):
        '''
        Constructor for the Trigger Server
        '''

        #sets the default config for the logging
        logging.basicConfig(filename='hfu_trigger_server.log', encoding='utf-8', level=logging.DEBUG)

        try:
            #checks if admin rights are present
            if self.check_elevation():
                #creates a seperate Thread for the actual TCP/IP Server
                self.server_thread = threading.Thread(name='server_thread', target=self.run_server)

                #searches for physical network adapters
                logging.debug("Extracting physical network devices...")
                self.nics = wmi.WMI().Win32_NetworkAdapter()
                self.nic_names = []

                #writes all physical adapters into a list
                for nic in self.nics:
                    if nic.PhysicalAdapter != False:
                        self.nic_names.append(nic.ProductName)

                #starts the gui
                logging.debug("Creating GUI Frame...")
                self.root = Tk()
                self.root.title("Trigger Server")
                self.root.minsize(300, 450)
                self.build_gui()
                self.root.mainloop()

        except:
            logging.exception("ERROR during program execution!")

    def check_elevation(self):
        '''
        Checks if program runs with admin rights.
        Promts for elevation if not.
        '''

        logging.debug("Checking elevation...")
        try:
            #already admin?
            if ctypes.windll.shell32.IsUserAnAdmin():

                logging.debug("Elevation present.")
                return True
            
            #ask for admin
            else:
                logging.info("Restart progam and ask for elevation...")
                ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        
        except:
            logging.exception("Elevation process failed. ")
            sys.exit()

    def build_gui(self):
        '''
        Builds and spawns all parts of the GUI.
        Sets up all necessary traces for intercations with the GUI.
        '''

        logging.debug("Building GUI...")

        #add a grid
        mainframe = Frame(self.root)
        mainframe.grid(column=0,row=0, sticky=(N,W,E,S) )
        mainframe.columnconfigure(0, weight = 1)
        mainframe.rowconfigure(0, weight = 1)
        mainframe.pack(pady = 50, padx = 50)

        #create the Tkinter variables for the dropdown
        self.tkvar_device = StringVar(self.root)
        self.tkvar_network = StringVar(self.root)
        self.tkvar_advanced = IntVar(self.root)

        #dictionarys with dropdown options
        choices_devices = ('fNIRS', 'Movisens EKG/EDA', 'Fahrsimulator', 'Motiontracker/EMG')
        choices_network = (self.nic_names)

        #sets the default options
        self.tkvar_device.set(choices_devices[0]) 
        self.tkvar_network.set(choices_network[0])

        #dropdown devices
        self.popupMenu = OptionMenu(mainframe, self.tkvar_device, *choices_devices)
        self.label_popup1 = Label(mainframe, text="Choose the software running here")
        self.label_popup1.grid(row = 1, column = 1)
        self.popupMenu.grid(row = 2, column =1)

        #dropdown network adapters
        Label(mainframe, text="").grid(row = 3, column = 1)
        self.popupMenu2 = OptionMenu(mainframe, self.tkvar_network, *choices_network)
        self.label_popup2 = Label(mainframe, text="Choose the network adapter")
        self.label_popup2.grid(row = 4, column = 1)
        self.popupMenu2.grid(row = 5, column =1)

        #chackbox for advanced usage
        Label(mainframe, text="").grid(row = 6, column = 1)
        self.check_btn = Checkbutton(mainframe, text = "Advanced Options", variable = self.tkvar_advanced, onvalue = 1, offvalue = 0, height=2, width = 20)
        self.check_btn.grid(row = 7, column = 1)

        #ip input
        self.label_ip = Label(mainframe, text="IP address:", width = 15, fg = "gray")
        self.label_ip.grid(row = 8, column = 1)
        self.text_ip = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
        self.text_ip.grid(row = 9, column = 1)

        #port input
        self.label_port = Label(mainframe, text="Port:", width = 15, fg = "gray")
        self.label_port.grid(row = 10, column = 1)
        self.text_port = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
        self.text_port.grid(row = 11, column = 1)

        #start/stop button
        Label(mainframe, text="").grid(row = 12, column = 1)
        self.btn_start = Button(mainframe, text = "Start", command = self.button_start)
        self.btn_start.grid(row = 13, column = 1)
        self.btn_stop = Button(mainframe, text = "Stop", state = DISABLED, command = self.button_stop)
        self.btn_stop.grid(row = 14, column = 1)

        #reset button
        Label(mainframe, text="").grid(row = 15, column = 1)
        self.label_reset = Label(mainframe, text = "Reset network configuration for\nthe selected network adapter.\nOnly if adapter is connected!", height = 3)
        self.label_reset.grid(row = 16, column = 1)
        self.btn_reset = Button(mainframe, text = "Reset", command = self.button_reset)
        self.btn_reset.grid(row = 17, column = 1)

        #trace for the advance usage checkbox
        self.tkvar_advanced.trace('w', self.change_advanced)
        
    def button_start(self, *args):
        '''
        Method for the reaction of the start button.
        Starts the server thread.

        param *args -> arguments passed by the button
        '''
        
        logging.debug("Start button pressed.")

        #disables buttons and dropdowns
        self.popupMenu['state'] = DISABLED
        self.popupMenu2['state'] = DISABLED
        self.check_btn['state'] = DISABLED

        #disables text inputs
        self.text_ip["state"] = DISABLED
        self.text_ip["bg"] = "light gray"
        self.text_port["state"] = DISABLED
        self.text_port["bg"] = "light gray"

        #enables stop button
        self.btn_start['state'] = DISABLED
        self.btn_stop['state'] = NORMAL
        self.btn_reset['state'] = DISABLED

        #changes color of labels
        self.label_popup1["fg"] = "gray"
        self.label_popup2["fg"] = "gray"
        self.label_ip["fg"] = "gray"
        self.label_port["fg"] = "gray"
        self.label_reset["fg"] = "gray"

        #starts the server thread
        logging.info("Starting server thread...")
        global stop_threads
        stop_threads = False
        self.server_thread.start()

    def button_stop(self, *args):
        '''
        Method for the reaction of the stop button.
        Stops the server thread.

        param *args -> arguments passed by the button
        '''

        #stops the server thread and closes the socket
        logging.info("Stopping the server thread...")
        global stop_threads
        global sock
        stop_threads = True
        sock.close()
        self.server_thread.join()

        print('\nServer stopped...')

        #enables buttons and dropdowns
        self.popupMenu['state'] = NORMAL
        self.popupMenu2['state'] = NORMAL
        self.check_btn['state'] = NORMAL

        #disables stop button
        self.btn_start['state'] = NORMAL
        self.btn_stop['state'] = DISABLED
        self.btn_reset['state'] = NORMAL

        #sets colors of labels to black
        self.label_popup1["fg"] = "black"
        self.label_popup2["fg"] = "black"
        self.label_reset["fg"] = "black"

        #requests the status of the advanced usage checkbox
        self.change_advanced()

    def button_reset(self, *args):
        '''
        Method for the reaction of the reset button.
        Resets the network configuration to DHCP for the given network adapter.
        Resets the firewall options.

        param *args -> arguments passed by the button
        '''
        
        logging.info("Resetting network and firewall options...")

        #resets the network configuration to DHCP
        ip, port = self.set_network_options(self.tkvar_device.get(), self.tkvar_network.get(), False)

        #resets the firewall configuration
        self.set_firewall_rule(port, False)

    def change_advanced(self, *args):
        '''
        Method for the reaction of the advanced usage checkbox.
        Checks the status of the chekcbox and sets the ip and port text input fields

        param *args -> arguments passed by the button
        '''

        #if advanced usage is disables
        if self.tkvar_advanced.get() == 0:
            #disables the ip and port text input
            self.text_ip["state"] = DISABLED
            self.text_ip["bg"] = "light gray"
            self.label_ip["fg"] = "gray"
            self.text_port["state"] = DISABLED
            self.text_port["bg"] = "light gray"
            self.label_port["fg"] = "gray"
        
        #if advanced usage is enabled
        else:
            #enables the ip and port text input
            self.text_ip["state"] = NORMAL
            self.text_ip["bg"] = "white"
            self.label_ip["fg"] = "black"
            self.text_port["state"] = NORMAL
            self.text_port["bg"] = "white"
            self.label_port["fg"] = "black"

    def set_network_options(self, device_name, network_adapter, set_network=True):
        '''
        Sets or resets the network configuration of the given network adapter

        param device_name       -> name of the device the server runs for
        param network_adapter   -> name of the selected network adapter
        param set_network       -> set or reset the network adapter? True => set; False => reset

        return -> selected ip and port in a list
        '''

        logging.info(f"Changing network configuration for {device_name} on {network_adapter}...")

        #Dictionary with default network configuration information
        switcher = {

            'fNIRS':                {'ip': u'192.168.1.2', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
            'Movisens EKG/EDA':     {'ip': u'192.168.1.3', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
            'Eyetracker':           {'ip': u'192.168.1.4', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
            'Motiontracker/EMG':    {'ip': u'192.168.1.5', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'},
            'Fahrsimulator':        {'ip': u'192.168.1.6', 'netmask': u'255.255.255.0', 'gateway': u'192.168.1.1'}
        }

        #gets the needed info from the dictionary
        network_options = switcher.get(device_name)

        #uses default ip if no ip is given in the advanced text input
        ip = network_options['ip']
        if self.text_ip.get("1.0",END) != '\n':
            ip = self.text_ip.get("1.0",END)

        #uses default port if no port is given in the advanced text input
        port = 10001
        if self.text_port.get("1.0",END) != '\n':
            port = int(self.text_port.get("1.0",END))

        #searches for the windows network config matching with the given adapter
        for nic in self.nics:
            if nic.ProductName == network_adapter:
                
                wmi_config = wmi.WMI().Win32_NetworkAdapterConfiguration(InterfaceIndex=nic.InterfaceIndex)

                #set new configuration
                if set_network:
                    wmi_config[0].EnableStatic(IPAddress=[ip],SubnetMask=[network_options['netmask']])
                    wmi_config[0].SetGateways(DefaultIPGateway=[network_options['gateway']])
                    logging.info(f"Changed network configuration of {network_adapter}\n\tto ip-{network_options['ip']}; netmask-{network_options['netmask']}; gateway-{network_options['gateway']}")
                    print(f"Changed network configuration of {network_adapter}\n\tto ip-{network_options['ip']}; netmask-{network_options['netmask']}; gateway-{network_options['gateway']}")

                #reset configuration
                else:

                    pass
                    #exit_code = wmi_config[0].EnableDHCP()
                    #if exit_code == 0:
                    #    logging.info(f"Changed network configuration of {network_adapter}\n\tto DHCP"")
                    #    print(f"Changed network configuration of {network_adapter}\n\tto DHCP")

                    #else:
                    #    logging.warning(f"Change of network configuration to DHCP\n\tfailed because adapter is not connected.")
                    #    print(f"Change of network configuration to DHCP\n\tfailed because adapter is not connected.")
                
                break
        
        #returns selected ip and port in a list
        return (ip, port)

    def set_firewall_rule(self, port, set_firewall=True):
        '''
        Sets or resets the firewall configuration

        param port          -> name of the port
        param set_firewall   -> set or reset the firewall adapter? True => set; False => reset
        '''

        logging.info(f"Changing firewall configuration on port {port}...")
        logging.debug(f"Checking if firewall rule on port {port} is present...")

        #checking if firewall already exist
        proc_check_present = subprocess.run(
            [
                'netsh', 'advfirewall', 'firewall',
                'show', 'rule', 'name=HFU_Trigger_Server'
            ], 
            check=True,
            capture_output=True
        )

        proc_output_list = proc_check_present.stdout.decode("ISO-8859-1").split("\r\n")
        proc_output_list = [i for i in proc_output_list if i]

        if (proc_output_list[-1] != "OK."):
            #creating new firewall rule if it doesn't exist
            logging.info(f'Creating new firewall rule on port {10001} with the name "HFU_Trigger_Server"...')

            subprocess.run(
                [
                    'netsh', 'advfirewall', 'firewall',
                    'add', 'rule', 'name=HFU_Trigger_Server',
                    'dir=in', 'action=allow', 'enable=no', 
                    'protocol=TCP', f'localport={port}'
                ], 
                check=True, 
                capture_output=True
            )

            print(f'New firewall rule on port {10001} with the name "HFU_Trigger_Server" created.')

        #enabling or disabling the present firewall rule
        logging.info(f'Setting firewall rule with name "HFU_Trigger_Server" to {"enabled" if set_firewall else "disabled"}...')

        subprocess.run(
            [
                'netsh', 'advfirewall', 'firewall',
                'set', 'rule', 'name=HFU_Trigger_Server',
                'new', f'enable={"yes" if set_firewall else "no"}'
            ],
            check=True,
            capture_output=True
        )

        print(f'Changed Firewall rule with name "HFU_Trigger_Server" to {"enabled" if set_firewall else "disabled"}.')

    def print_description(self, device_name):
        '''
        Prints the Howto Description of the selected device to stdout

        param device_name -> name of the device the description should be printed for
        '''

        logging.debug("Print description...")

        #dictionary with all descriptions
        switcher = {

            'fNIRS': 'Start Oxysoft with administrator rights.\n'
                        'Start a measurement and change to the XXXX view.\n'
                        'Send a test trigger and check if it arrived.',
            'Movisens EKG/EDA': 'Coming soon...',
            'Eyetracker': 'Coming soon...',
            'Motiontracker/EMG': 'Start CAPTIV with administrator rights.\n'
                                    'Start a measurement and place the cursor above the trigger button.\n'
                                    'Make sure that the CAPTIV window is in foreground.\n'
                                    'Send a test trigger and check if the trigger value in CAPTIV increased.\n'
                                    '\n'
                                    'WARNING: The highest trigger value is XXX. The following trigger will\n'
                                    'reset the value and stop the measurement. Make sure you have enough\n'
                                    'trigger values left!',
            'Fahrsimulator': 'Start the driving simulator.\n'
                                'Send a test trigger and check if it arrived.\n'
                                'The triggers will be stored in this directory as csv files.\n'
                                'You have to restart this server for every participant.'
        }

        #prints the description
        print('\nDESCRIPTION:')
        print(switcher.get(device_name))
        print('\n')

    def run_server(self):
        '''
        Starts the trigger server in a new thread
        Performs the received triggers device dependant
        '''

        pythoncom.CoInitialize()
        #gets device name from dropdown box
        device_name = self.tkvar_device.get()

        logging.info(f'Server for {device_name} selected...')

        #configuration of network
        ip, port = self.set_network_options(device_name, self.tkvar_network.get())
        #configuration of the firewall
        self.set_firewall_rule(port)
        #prints the device description
        self.print_description(device_name)

        #waiting for network configuration
        time.sleep(5)

        #starts up the network socket
        global sock
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip, port)
        print(f'Server for {device_name} selected...')
        print('Starting up trigger server on %s on %s' % server_address)
        logging.info('Starting up trigger server on %s on %s' % server_address)
        sock.bind(server_address)

        #starts to listen on the socket
        sock.listen(1)

        #creates mouse object for click actions
        mouse_object = mouse.Controller()
        #saves the server start time
        start_time = int(round(time.time() * 1000))
        logging.info(f"Started server. Time: {start_time}")
        trigger_count = 0

        #waiting for incoming connection
        while True:

            print('Waiting for connection')
            try:
                connection, client_address = sock.accept()

            finally:
                logging.info("Socket closed.")
                print('Socket closed...')
                break

            #waits for server stop action
            global stop_threads
            if stop_threads == True:
                break
            
            try:
                trigger_count = trigger_count + 1
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
                        print('No more data from ', client_address)
                        break
                
                #performs the trigger and sved the internal latency
                internal_latency_start =  int(round(time.time() * 1000))
                #splits the trigger information
                trigger_parts = received_message.split("%SEP%")

                logging.info(f"Performing trigger {trigger_count} for device {device_name}.")
                print(f"Performing trigger {trigger_count} for device {device_name}.")

                #chooses the current device
                if device_name == 'fNIRS':
                    self.trigger_fnirs(trigger_parts)
                elif device_name == 'Movisens EKG/EDA':
                    self.trigger_movisens(trigger_parts)
                elif device_name == 'Eyetracker':
                    self.trigger_eyetracker(trigger_parts)
                elif device_name == 'Motiontracker/EMG':
                    self.trigger_motion(trigger_parts, mouse_object)
                elif device_name == 'Fahrsimulator':
                    self.trigger_driving(trigger_parts, start_time)

                #calculation of internal latency
                internal_latency = int(round(time.time() * 1000)) - internal_latency_start
                logging.info(f"Trigger {trigger_count} for device {device_name} performed. Internal latnecy - {internal_latency}ms\n")
                print(f"Trigger {trigger_count} for device {device_name} performed. Internal latnecy - {internal_latency}ms\n")

            except:
                logging.exception("ERROR during trigger performance")
                    
            finally:
                connection.close()

    def trigger_fnirs(self, message):
        '''
        Performs the trigger action on this device for the fNIRS Software
        Sends trigger to DCOM device

        param message -> received trigger message from the remot client
        '''

        pass

    def trigger_motion(self, message, mouse_object):
        '''
        Performs the trigger action on this device for the Motiontracker/EMG Software
        Performs mous click with the left button

        param message       -> received trigger message from the remot client
        param mouse_object  -> object for performing the mouse click
        '''

        #perform mouse click
        mouse_object.click(mouse.Button.left, 1)

    def trigger_movisens(self, message):
        '''
        Performs the trigger action on this device for the Movisens Software

        param message -> received trigger message from the remot client
        '''

        pass

    def trigger_driving(self, message, start_time):
        '''
        Performs the trigger action on this device for the driving simulator Software
        Saves trigger with timestamp in seperate file

        param message   -> received trigger message from the remot client
        start_time      -> trigger time to store in the file
        '''

        # stores the trigger in the file
        file = open("".join((str(start_time), ".csv")),"a")
        file.write("".join((str(int(round(time.time() * 1000))), ";", message[0], ";", message[1])))
        file.close()

    def trigger_eyetracker(self, message):
        '''
        Performs the trigger action on this device for the Eyetracker Software

        param message -> received trigger message from the remot client
        '''

        pass


#starts the trigger server program
tr_srv = HFU_Trigger_Server()