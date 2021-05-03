from tkinter import *
import tkinter as ttk
#from ttk import *
import psutil

addrs = psutil.net_if_addrs()
print()

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
choices_devices = ('Oxysoft', 'Movisens SensorManager')
choices_network = list(addrs.keys())

tkvar_device.set(choices_devices[0]) # set the default option
tkvar_network.set(choices_network[0])

def button_submit(*args):
    print("Submit")

popupMenu = OptionMenu(mainframe, tkvar_device, *choices_devices)
Label(mainframe, text="Choose the software running here").grid(row = 1, column = 1)
popupMenu.grid(row = 2, column =1)

Label(mainframe, text="").grid(row = 3, column = 1)

popupMenu2 = OptionMenu(mainframe, tkvar_network, *choices_network)
Label(mainframe, text="Choose the network adapter").grid(row = 4, column = 1)
popupMenu2.grid(row = 5, column =1)

Label(mainframe, text="").grid(row = 6, column = 1)

Checkbutton(mainframe, text = "Advanced Options", variable = tkvar_advanced, onvalue = 1, offvalue = 0, height=2, width = 20).grid(row = 7, column = 1)

label_ip = Label(mainframe, text="IP address:", width = 15, fg = "gray")
label_ip.grid(row = 8, column = 1)
text_ip = Text(mainframe, height = 1, width = 15, bg = "light gray")
text_ip.grid(row = 9, column = 1)

label_port = Label(mainframe, text="Port:", width = 15, fg = "gray")
label_port.grid(row = 10, column = 1)
text_port = Text(mainframe, height = 1, width = 15, bg = "light gray")
text_port.grid(row = 11, column = 1)

Label(mainframe, text="").grid(row = 12, column = 1)

Button(mainframe, text = "Submit", command = button_submit).grid(row = 13, column = 1)

# on change dropdown value
def change_dropdown_device(*args):
    print( tkvar_device.get() )

def change_dropdown_network(*args):
    print( tkvar_network.get() )

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
tkvar_device.trace('w', change_dropdown_device)
tkvar_network.trace('w', change_dropdown_network)
tkvar_advanced.trace('w', change_advanced)

root.mainloop()