import threading
from tkinter import *
from tkinter import ttk
import socket
import subprocess
import sys
import logging
import time
import wmi
import ctypes

class HFU_Trigger_Client():

    def __init__(self, network_adapter = None):

        logging.basicConfig(filename="hfu_trigger_client.log", level=logging.DEBUG)

        self.network_adaper = network_adapter

        try:
            if self.network_adaper == None:
                #checks if admin rights are present
                if self.check_elevation():
                    self.activation = {
                        'fNIRS':        False, 
                        'Motion':       False, 
                        'Eyetracker':   False, 
                        'Movisens':     False, 
                        'Driving':      False
                    }

                    #searches for physical network adapters
                    logging.debug("Extracting physical network devices...")
                    self.nics = wmi.WMI().Win32_NetworkAdapter()
                    self.nic_names = []

                    #writes all physical adapters into a list
                    for nic in self.nics:
                        if nic.PhysicalAdapter != False:
                            self.nic_names.append(nic.ProductName)

                    
                    logging.debug("Creating GUI Frame...")
                    self.root = Tk()
                    self.root.title("Trigger Client")
                    self.root.minsize(300, 450)
                    self.build_gui()
                    self.root.mainloop()
            
            else:
                self.activation = {
                    'fNIRS':        False, 
                    'Motion':       False, 
                    'Eyetracker':   False, 
                    'Movisens':     False, 
                    'Driving':      False
                }

                #searches for physical network adapters
                logging.debug("Extracting physical network devices...")
                self.nics = wmi.WMI().Win32_NetworkAdapter()
                self.nic_names = []

                #writes all physical adapters into a list
                for nic in self.nics:
                    if nic.PhysicalAdapter != False:
                        self.nic_names.append(nic.ProductName)

                self.configure_no_gui(self.network_adaper)

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

    def configure_no_gui(self, adapter_name, set=True):
        '''
        '''

        if set:
            ip, port = self.set_network_options(adapter_name)
            self.set_firewall_rule(port)
        else:
            ip, port = self.set_network_options(adapter_name, False)
            self.set_firewall_rule(port, False)

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
        choices_devices = ('fNIRS', 'Movisens EKG/EDA', 'Eyetracker', 'Driving Simulator', 'Motiontracker/EMG')
        choices_network = (self.nic_names)

        #sets the default options
        self.tkvar_network.set(choices_network[0])

        #dropdown devices
        self.popupMenu = Listbox(mainframe, selectmode = "multiple", height=4)
        self.label_popup1 = Label(mainframe, text="Choose the target devices")
        self.label_popup1.grid(row = 1, column = 1)
        self.popupMenu.grid(row = 2, column =1)
        
        for device in choices_devices:
            self.popupMenu.insert(END, device)

        #dropdown network adapters
        Label(mainframe, text="").grid(row = 3, column = 1)
        self.popupMenu2 = OptionMenu(mainframe, self.tkvar_network, *choices_network)
        self.label_popup2 = Label(mainframe, text="Choose the network adapter")
        self.label_popup2.grid(row = 1, column = 2)
        self.popupMenu2.grid(row = 2, column =2)

        #start/stop button
        Label(mainframe, text="").grid(row = 3, column = 2)
        ttk.Separator(mainframe,orient=HORIZONTAL).grid(row=4, column=1, columnspan=2, sticky="ew")
        Label(mainframe, text="").grid(row = 5, column = 1, columnspan=2)
        self.btn_set = Button(mainframe, text = "Set configuration", command = self.button_set)
        self.btn_set.grid(row = 6, column = 1)
        self.btn_reset = Button(mainframe, text = "Reset configuration", state = DISABLED, command = self.button_reset)
        self.btn_reset.grid(row = 7, column = 1)

        #reset button
        self.label_reset = Label(mainframe, text = "Perform manual trigger", height = 1)
        self.label_reset.grid(row = 6, column = 2)
        self.btn_trigger = Button(mainframe, state=DISABLED, text = "Trigger", command = self.button_trigger)
        self.btn_trigger.grid(row = 7, column = 2)

        #checkbox for advanced usage
        Label(mainframe, text="").grid(row = 8, column = 1, columnspan=2)
        ttk.Separator(mainframe,orient=HORIZONTAL).grid(row=9, column=1, columnspan=2, sticky="ew")
        self.check_btn = Checkbutton(mainframe, text = "Advanced Options", variable = self.tkvar_advanced, onvalue = 1, offvalue = 0, height=2, width = 20)
        self.check_btn.grid(row = 10, column = 1, columnspan=2)

        #ip input
        self.label_ip = Label(mainframe, text="IP address:", width = 15, fg = "gray")
        self.label_ip.grid(row = 11, column = 1, columnspan=2)
        self.text_ip = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
        self.text_ip.grid(row = 12, column = 1, columnspan=2)

        #port input
        self.label_port = Label(mainframe, text="Port:", width = 15, fg = "gray")
        self.label_port.grid(row = 13, column = 1, columnspan=2)
        self.text_port = Text(mainframe, state = DISABLED, height = 1, width = 15, bg = "light gray")
        self.text_port.grid(row = 14, column = 1, columnspan=2)

        #console text view
        Label(mainframe, text="").grid(row = 15, column = 1, columnspan=2)
        ttk.Separator(mainframe,orient=HORIZONTAL).grid(row=16, column=1, columnspan=2, sticky="ew")
        Label(mainframe, text="", height=1).grid(row = 17, column = 1, columnspan=2)
        self.console_text = Text(mainframe, height=10)
        self.console_text.grid(row = 18, column = 1, columnspan=2)

        #redirecting standard output and standard error to console text view
        redir = RedirectText(self.console_text)
        sys.stdout = redir
        sys.stderr = redir

        #trace for the advance usage checkbox
        self.tkvar_advanced.trace('w', self.change_advanced)

        #set default exit on close operation
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)

    def close_application(self):
        '''
        Method for the default close operation of the application window
        '''

        self.button_reset()
        self.root.destroy()

    def button_set(self, *args):
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
        self.btn_set['state'] = DISABLED
        self.btn_reset['state'] = NORMAL
        self.btn_trigger['state'] = NORMAL

        #changes color of labels
        self.label_popup1["fg"] = "gray"
        self.label_popup2["fg"] = "gray"
        self.label_ip["fg"] = "gray"
        self.label_port["fg"] = "gray"
        self.label_reset["fg"] = "gray"

        #setting server options
        logging.info("Setting trigger options...")

        active_devices_index = self.popupMenu.curselection()
        active_devices = []
        for i in  active_devices_index:
            active_devices.append(self.popupMenu.get(i))

        if "fNIRS" in active_devices:
            self.changeActivationFNIRS()
        if "Motiontracker/EMG" in  active_devices:
            self.changeActivationMotion()
        if "Movisens EKG/EDA" in active_devices:
            self.changeActivationMovisens()
        if "Driving Simulator" in active_devices:
            self.changeActivationDriving()
        if "Eyetracker" in active_devices:
            self.changeActivationEyetracker()

        ip, port = self.set_network_options(self.tkvar_network.get())
        self.set_firewall_rule(port)
        
    def button_reset(self, *args):
        '''
        Method for the reaction of the stop button.
        Stops the server thread.

        param *args -> arguments passed by the button
        '''

        #reset trigger options
        logging.info("Reset the trigger options...")
        
        active_devices_index = self.popupMenu.curselection()
        active_devices = []
        for i in  active_devices_index:
            active_devices.append(self.popupMenu.get(i))
            
        if "fNIRS" in active_devices:
            self.changeActivationFNIRS()
        if "Motiontracker/EMG" in  active_devices:
            self.changeActivationMotion()
        if "Movisens EKG/EDA" in active_devices:
            self.changeActivationMovisens()
        if "Driving Simulator" in active_devices:
            self.changeActivationDriving()
        if "Eyetracker" in active_devices:
            self.changeActivationEyetracker()
        
        ip, port = self.set_network_options(self.tkvar_network.get(), False)
        self.set_firewall_rule(port, False)

        #enables buttons and dropdowns
        self.popupMenu['state'] = NORMAL
        self.popupMenu2['state'] = NORMAL
        self.check_btn['state'] = NORMAL

        #disables stop button
        self.btn_set['state'] = NORMAL
        self.btn_reset['state'] = DISABLED
        self.btn_trigger['state'] = DISABLED

        #sets colors of labels to black
        self.label_popup1["fg"] = "black"
        self.label_popup2["fg"] = "black"
        self.label_reset["fg"] = "black"

        #requests the status of the advanced usage checkbox
        self.change_advanced()

    def button_trigger(self):
        self.sendTrigger("M", "Manual_Trigger")

    def change_advanced(self):
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

    def set_network_options(self, network_adapter, set_network=True):
        '''
        Sets or resets the network configuration of the given network adapter

        param network_adapter   -> name of the selected network adapter
        param set_network       -> set or reset the network adapter? True => set; False => reset

        return -> selected ip and port in a list
        '''

        logging.info(f"Changing network configuration on {network_adapter}...")

        netmask = u'255.255.255.0'
        gateway = u'192.168.1.1'

        #uses default ip if no ip is given in the advanced text input
        ip = '192.168.1.20'
        if self.network_adaper == None:
            if self.text_ip.get("1.0",END) != '\n':
                ip = self.text_ip.get("1.0",END)

        #uses default port if no port is given in the advanced text input
        port = 10001
        if self.network_adaper == None:
            if self.text_port.get("1.0",END) != '\n':
                port = int(self.text_port.get("1.0",END))

        #searches for the windows network config matching with the given adapter
        for nic in self.nics:
            if nic.ProductName == network_adapter:
                
                wmi_config = wmi.WMI().Win32_NetworkAdapterConfiguration(InterfaceIndex=nic.InterfaceIndex)

                #set new configuration
                if set_network:
                    wmi_config[0].EnableStatic(IPAddress=[ip],SubnetMask=[netmask])
                    wmi_config[0].SetGateways(DefaultIPGateway=[gateway])
                    logging.info(f"Changed network configuration of {network_adapter}\n\tto ip-{ip}; netmask-{netmask}; gateway-{gateway}")
                    print(f"Changed network configuration of {network_adapter}\n\tto ip-{ip}; netmask-{netmask}; gateway-{gateway}")

                #reset configuration
                else:
                    test = proc_check_present = subprocess.run(
                        [
                            'netsh', 'interface', 'ipv4', 'set',
                            'address', f'name={nic.NetConnectionID}', 'source=dhcp'
                        ],
                        capture_output=True
                    )
                    
                    logging.info(f"Changed network configuration of {network_adapter}\n\tto DHCP")
                    print(f"Changed network configuration of {network_adapter}\n\tto DHCP")
                
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
            #check=True,
            capture_output=True
        )

        proc_output_list = proc_check_present.stdout.decode("ISO-8859-1").split("\r\n")
        proc_output_list = [i for i in proc_output_list if i]

        if (proc_output_list[-1] != "OK."):
            #creating new firewall rule if it doesn't exist
            logging.info(f'Creating new firewall rule on port {port} with the name "HFU_Trigger_Server"...')

            subprocess.run(
                [
                    'netsh', 'advfirewall', 'firewall',
                    'add', 'rule', 'name=HFU_Trigger_Server',
                    'dir=out', 'action=allow', 'enable=no', 
                    'protocol=TCP', f'localport={port}'
                ], 
                check=True, 
                capture_output=True
            )

            print(f'New firewall rule on port {port} with the name "HFU_Trigger_Server" created.')

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

    def changeActivationFNIRS(self):
        if self.activation["fNIRS"]:
            self.activation["fNIRS"] = False
        else:
            self.activation["fNIRS"] = True

    def changeActivationMotion(self):
        if self.activation["Motion"]:
            self.activation["Motion"] = False
        else:
            self.activation["Motion"] = True

    def changeActivationEyetracker(self):
        if self.activation["Eyetracker"]:
            self.activation["Eyetracker"] = False
        else:
            self.activation["Eyetracker"] = True

    def changeActivationMovisens(self):
        if self.activation["Movisens"]:
            self.activation["Movisens"] = False
        else:
            self.activation["Movisens"] = True

    def changeActivationDriving(self):
        if self.activation["Driving"]:
            self.activation["Driving"] = False
        else:
            self.activation["Driving"] = True

    def sendTrigger(self, triggerLetter, triggerText):

        self.connectionInfo = {
            'fNIRS':        {'ip': u'192.168.1.2', 'port': 10001},
            'Movisens':     {'ip': u'192.168.1.3', 'port': 10001},
            'Eyetracker':   {'ip': u'192.168.1.4', 'port': 10001},
            'Motion':       {'ip': u'192.168.1.5', 'port': 10001},
            'Driving':      {'ip': u'192.168.1.6', 'port': 10001}
        }

        for device in self.activation.keys():
            if self.activation.get(device):
                t = threading.Thread(target=self.createTriggerSocket, args=(device, self.connectionInfo[device]["ip"], self.connectionInfo[device]["port"], triggerLetter, triggerText))
                t.start()

    def createTriggerSocket(self, device, ip, port, triggerLetter, triggerText):
        
        socketCon = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip, port)
        
        trigger_start_time = int(round(time.time() * 1000))
        logging.info(f"Sending trigger for device {device} to {ip} on port {port}. system time: {trigger_start_time}")
        
        try:
            socketCon.connect(server_address)
            message = "{}%SEP%{}".format(triggerLetter, triggerText)

            #logging.info("nirs message: {}".format(message))
            socketCon.sendall(message.encode("utf-8"))
            
            amount_received = 0
            amount_expected = len(message)
            
            received_message = ""

            while amount_received < amount_expected:
                data = socketCon.recv(32)
                amount_received += len(data)
                received_message = "".join((received_message, data.decode("utf-8")))
                
            if message == received_message:
                trigger_stop_time = int(round(time.time() * 1000))
                trigger_latency = trigger_stop_time - trigger_start_time
                logging.info(f"Trigger for device {device} successful. System time: {trigger_stop_time}; Two-way-latency: {trigger_latency}ms")
                
            else:
                logging.error(f"Trigger to device {device} failed. Messages not matching. Received message: {received_message}")
                
        except:
            logging.exception(f"Error while sending trigger to device {device}")
                
        finally:
            socketCon.close()

class RedirectText(object):
    '''
    Class for redirecting stdout and stderr to a text view
    '''

    def __init__(self, text_ctrl):
        '''
        Constructor for the redirector
        '''

        #setting the text view
        self.output = text_ctrl
        
    def write(self, string):
        '''
        Write a message to the text view
        '''

        #writes given text to text view
        self.output.insert(END, string)
        self.output.see("end")

    def flush(self):
        '''
        Passes the standard flush method of the sys output
        '''
        pass