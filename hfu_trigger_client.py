from multiprocessing import Process
from tkinter import *
import tkinter as ttk
import socket
import sys
import logging
import time
import wmi

class HFU_Trigger_Client():

    def __init__(self, gui=False):

        logging.basicConfig(filename="HFU_Trigger_Client.log", level=logging.DEBUG)

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

        if gui:
            logging.debug("Creating GUI Frame...")
            self.root = Tk()
            self.root.title("Trigger Client")
            self.root.minsize(300, 450)
            self.build_gui()
            self.root.mainloop()

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
        self.popupMenu = Listbox(mainframe, selectmode = "multiple", height=5)
        self.label_popup1 = Label(mainframe, text="Choose the target devices")
        self.label_popup1.grid(row = 1, column = 1)
        self.popupMenu.grid(row = 2, column =1)
        
        for device in choices_devices:
            self.popupMenu.insert(END, device)

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
        self.btn_start = Button(mainframe, text = "Set", command = self.button_set)
        self.btn_start.grid(row = 13, column = 1)
        self.btn_stop = Button(mainframe, text = "Reset", state = DISABLED, command = self.button_reset)
        self.btn_stop.grid(row = 14, column = 1)

        #reset button
        Label(mainframe, text="").grid(row = 15, column = 1)
        self.label_reset = Label(mainframe, text = "Perform manual trigger", height = 1)
        self.label_reset.grid(row = 16, column = 1)
        self.btn_reset = Button(mainframe, text = "Trigger", command = self.button_trigger)
        self.btn_reset.grid(row = 17, column = 1)

        #trace for the advance usage checkbox
        self.tkvar_advanced.trace('w', self.change_advanced)

    def button_set(self):
        pass

    def button_reset(self):
        pass

    def button_trigger(self):
        pass

    def change_advanced(self):
        pass

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

        for device in self.activation.keys:
            if self.activation.get(device):
                p = Process(target=createTriggerSocket, args=(device, self.connectionInfo[device]["ip"], self.connectionInfo[device]["port"], triggerLetter, triggerText))
                p.start()

    def createTriggerSocket(self, device, ip, port, triggerLetter, triggerText):
        
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip, port)
        
        trigger_start_time = time.time()
        logging.info(f"Sending trigger for device {device} to {ip} on port {port}. system time: {trigger_start_time}")
        
        try:
            socket.connect(server_address)
            message = "{}%SEP%{}".format(triggerLetter, triggerText)

            #logging.info("nirs message: {}".format(message))
            socket.sendall(message.encode("utf-8"))
            
            amount_received = 0
            amount_expected = len(message)
            
            received_message = ""

            while amount_received < amount_expected:
                data = socket.recv(32)
                amount_received += len(data)
                received_message = "".join((received_message, data.decode("utf-8")))
                
            if message == received_message:
                trigger_stop_time = time.time()
                trigger_latency = trigger_stop_time - trigger_start_time
                logging.info(f"Trigger for device {device} successful. System time: {trigger_stop_time}; Two-way-latency: {trigger_latency}")
                
            else:
                logging.error(f"Trigger to device {device} failed. Messages not matching. Received message: {received_message}")
                
        except:
            logging.exception(f"Error while sending trigger to device {device}")
                
        finally:
            socket.close()

trigger_client = HFU_Trigger_Client(True)