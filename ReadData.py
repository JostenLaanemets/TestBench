import serial
import time
import tkinter as tk
from tkinter.filedialog import asksaveasfile
import serial.tools.list_ports
import threading
import csv

# Variables

startReading = False
ser1 = None
ser2 = None


# Function to list available serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
################################################################################
# Initialize the serial ports based on selected ports
def initialize_serial(port1, port2, currentBaudrate):
    global ser1, ser2
    #Baudrates, make them changeable?
    #Connection for first port
    
    try:
        ser1 = serial.Serial(
            port=port1,
            baudrate=currentBaudrate,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS
        )
        
        if ser1.is_open :
            print(f"Connected to {port1}")
            data1.config(text="Connected",background='green')
            
            
    except serial.SerialException:
        print(f"Failed to connect to {port1}")
        data1.config(text="Connection Failed", background='red')
        
        ser1 = None
    #Connection for second port
    try:
        ser2 = serial.Serial(
            port=port2,
            baudrate=currentBaudrate,
            parity=serial.PARITY_ODD,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS
        )
        if ser2.is_open :
            print(f"Connected to {port2}")
            data2.config(text="Connected", background='green')
            
            
    except serial.SerialException:
        print(f"Failed to connect to {port2}")
        data2.config(text="Connection Failed",background='red')
        
        ser2 = None
###############################################################################

# Data cleaning and decodeing from unnecessary characters
def cleanData(serialIn):
    try:
        dataCleaning = serialIn.readline()
        dataCleaning = dataCleaning.decode('utf-8').strip()
        if dataCleaning:  
            dataCleaning = ' '.join(dataCleaning.split())
            return float(dataCleaning)/10.0
        else:
            
            return 0.0
    except ValueError:
        print("Failed data cleaning")
        return 0.0


###############################################################################
# Start or stop reading data from serial ports
def start_reading():
    global i, startReading
    
    if startReading:
        startReading = False
        readButton.config(text="Start Read Serial")
        current_time = time.time_ns()
        print("Stopped reading")
    else:
        startReading = True
        readButton.config(text="Stop Reading Serial")
        print("Started reading")
        #For running read loop in the background so GUI is usable
        threading.Thread(target=read_loop, daemon=True).start()
###############################################################################

def writeToFile(d1,d2,ts):
    with open('DataLog.csv', 'a') as file:
        w=csv.writer(file, quoting=csv.QUOTE_ALL)
        w.writerow([d1,d2,ts])

# Loop to continuously read from the serial ports
def read_loop():
    global startReading, current_time
    dataOut1 = 0.0
    dataOut2 = 0.0
    start_time = time.time()  
    elapsed_time = 0.0
    while startReading:
        #Timestamp from the start of data reading
        
        current_time = time.time() * 1000
        
        if ser1 :
            dataOut1 = cleanData(ser1)
            data1.config(text=f'{dataOut1}', background='#16A085')
            
            
        if ser2:
            dataOut2 = cleanData(ser2)
            data2.config(text=f'{dataOut2}', background='#16A085')

        if dataOut1 or dataOut2:
            last_time = elapsed_time 
            elapsed_time = current_time - (start_time * 1000) 
            elapsed_time= f'{elapsed_time:.0f}'

            timestamp.config(text=f'Time: {elapsed_time} ms')
            if last_time != elapsed_time:
                writeToFile(dataOut1,dataOut2,elapsed_time)        


###############################################################################
# Function to connect to selected ports
def connect_ports():
    try:
        selected_port1 = port_var1.get()
        selected_port2 = port_var2.get()
        selected_baudrate = baudrateVars.get()
        baudRate_Menu.config(background="#d9d9d9")
        
        initialize_serial(selected_port1, selected_port2, selected_baudrate)
    except ValueError:
        baudRate_Menu.config(background="Red")
        
        

def refresh_ports():
    ports = list_serial_ports()
    
    saveP1 = port_var1.get()
    saveP2 = port_var2.get()

    port_menu1['menu'].delete(0, 'end')
    port_menu2['menu'].delete(0, 'end')
    
    for port in ["None"] + ports:
        port_menu1['menu'].add_command(label=port, command=tk._setit(port_var1, port))
        port_menu2['menu'].add_command(label=port, command=tk._setit(port_var2, port))

    if saveP1 in ports:
        port_var1.set(saveP1)
    else:
        port_var1.set("Select Port 1")
        data1.config(text="",background='#d9d9d9')

    if saveP2 in ports:
        port_var2.set(saveP2)
    else:
        port_var2.set("Select Port 2")
        data2.config(text="",background='#d9d9d9')

###############################################################################
def select_directory():
    selected_dir = tk.filedialog.askdirectory()
    if selected_dir:
        save_directory.set(selected_dir)

def writeToFile(d1, d2, ts):
    if save_checkbox_var.get():  # Check if saving is enabled
        file_path = f"{save_directory.get()}/{file_name_var.get()}"
        with open(file_path, 'a') as file:
            w = csv.writer(file, quoting=csv.QUOTE_ALL)
            w.writerow([d1, d2, ts])




###############################################################################
# GUI Function
def GUI():
    s = tk.Tk()
    s.title("Data Reading")
    s.geometry("1000x400")
    
    global readButton, port_var1, port_var2, baudrateVars, baudRate_Menu, data1, data2, timestamp , port_menu2, port_menu1
    global save_directory, save_checkbox_var, file_name_var
    ###########################################################################
    #Save to Directory
    save_directory = tk.StringVar()
    save_directory.set("Select Directory")

    file_name_var = tk.StringVar()
    file_name_var.set("DataLog.csv")  
    
    save_checkbox_var = tk.BooleanVar()
    save_checkbox_var.set(True)
    

    file_frame = tk.Frame(s)
    file_name_entry = tk.Entry(file_frame, textvariable=file_name_var, font=("Arial", 12), width=20)
    file_name_label = tk.Label(file_frame, text="CSV File Name:", font=("Arial", 12))
    save_checkbox = tk.Checkbutton(file_frame, text="Save Data to CSV", variable=save_checkbox_var)
    
    save_checkbox.pack(side='top', padx=5, anchor='w')
    file_name_label.pack(side='top', padx=5, anchor='w')
    file_name_entry.pack(side='bottom', padx=5, anchor='w')

    directory_frame = tk.Frame(s)
    directory_label = tk.Label(directory_frame, textvariable=save_directory, font=("Arial", 12), width=0, anchor='w')
    directory_button = tk.Button(directory_frame, text="Select Directory", command=select_directory, anchor='w')
    

    directory_button.pack(side='top', padx=5, anchor='w')
    directory_label.pack(side='bottom', padx=5, anchor='w')
    
    
    
    

     
    # Dropdown for first port
    port_var1 = tk.StringVar()
    port_var1.set("Select Port 1")
    ports1 = ["None"] + list_serial_ports()
    port_menu1 = tk.OptionMenu(s, port_var1, *ports1)
    port_menu1.configure(padx=50, pady=10, width=10)
    ###############################################################

    # Dropdown for second port
    port_var2 = tk.StringVar()
    port_var2.set("Select Port 2")
    ports2 = ["None"] +list_serial_ports()
    port_menu2 = tk.OptionMenu(s, port_var2, *ports2)    
    port_menu2.configure(padx=50, pady=10, width=10)
    ##############################################################


    # Dropdown for first port
    baudrateVars = tk.StringVar()
    baudrateVars.set("Select Baudrate")
    rates = [9600, 19200, 38400, 57600] 
    baudRate_Menu = tk.OptionMenu(s, baudrateVars, *rates)
    baudRate_Menu.configure(padx=50, pady=10, width=10)
    ###############################################################


    connectFrame = tk.Frame(s)


    # Connect button to initialize the ports
    connectButton = tk.Button(connectFrame, 
                               text="Connect to ports", 
                               command=connect_ports,
                               background="#229954",
                               activebackground='green',
                               activeforeground='white', 
                               fg="black",
                               cursor="hand2",
                               bd= 3,
                               highlightbackground="black",
                               highlightthickness=2,
                               font=("Arial", 12),
                               height=1, 
                               width=13)
    

    refreshButton = tk.Button(connectFrame, 
                               text="Refresh", 
                               command=refresh_ports,
                               background='#3498DB',
                               activebackground='#1F618D',
                               activeforeground='white', 
                               fg="black",
                               cursor="hand2",
                               bd= 3,
                               anchor='w',
                               highlightbackground="black",
                               highlightthickness=2,
                               font=("Arial", 12),
                               height=1, 
                               width=6)
    
    connectButton.pack(side='top', padx=0, pady=0, anchor='w')
    refreshButton.pack(side='bottom', padx=1, pady=10, anchor='w')

    # Button to start reading data
    readButton = tk.Button(s, 
                    text="Start Reading Serial", 
                    command=start_reading,
                    background='#3498DB',
                    activebackground="#1F618D", 
                    activeforeground="white",
                    anchor="center",
                    bd=3,
                    cursor="hand2",
                    disabledforeground="gray",
                    fg="black",
                    font=("Arial", 16),
                    height=2,
                    highlightbackground="black",
                    highlightcolor="green",
                    highlightthickness=2,
                    justify="center",
                    
                    padx=10,
                    pady=5,
                    width=18)

    d1Frame = tk.Frame(s)
    d2Frame = tk.Frame(s)   
    tsFrame = tk.Frame(s)
    # Data
    colorData = "#616A6B"
    data1 = tk.Label(d1Frame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    anchor='s',
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 20),
                    height=1, 
                    width=15)
    

    data2 = tk.Label(d2Frame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 20),
                    height=1, 
                    width=15)
    
    
    timestamp = tk.Label(tsFrame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 20),
                    height=1, 
                    width=15)

    colorLable='#3498DB'
    dataLable1 = tk.Label(d1Frame,
                    text="Var_1",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 12),
                    height=1, 
                    width=25)
    
    dataLable2 = tk.Label(d2Frame,
                    text="Var_2",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 12),
                    height=1, 
                    width=25)

    timeLable1 = tk.Label(tsFrame,
                    text="Timestamp",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    highlightbackground="black",
                    highlightthickness=2,
                    font=("Arial", 12),
                    height=1, 
                    width=25)

    data1.pack(side='bottom', padx=0, pady=0)
    dataLable1.pack(side='top', padx=0, pady=0)

    data2.pack(side='bottom', padx=0, pady=0)
    dataLable2.pack(side='top', padx=0, pady=0)
    
    timestamp.pack(side='bottom', padx=0, pady=0)
    timeLable1.pack(side='top', padx=0, pady=0)

    
#GRID
    port_menu1.grid(row=0, column=0, padx=10, pady=5, )
    port_menu2.grid(row=0, column=1, padx=10, pady=5, )
    connectFrame.grid(row=0, column=3, pady=5, padx=10, )
    baudRate_Menu.grid(row=0, column=2, padx=10, pady=5, )

    readButton.grid(row=2, column=0, pady=20, padx=10, )

    d1Frame.grid(row=1, column=0, pady=10, padx=10, )
    d2Frame.grid(row=1, column=1, pady=10, padx=10, )
    tsFrame.grid(row=1, column=2, pady=10, padx=10, )

    directory_frame.grid(row=2, column=1, pady=10, padx=10, columnspan=2, sticky='w')
    #save_checkbox.grid(row=3, column=2, pady=10, padx=10)
    file_frame.grid(row=2, column=2, pady=10, padx=10, sticky='w')

    s.mainloop()



if __name__ == "__main__":
    GUI()


