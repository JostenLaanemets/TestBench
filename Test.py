import serial
import time
import tkinter as tk
from tkinter.filedialog import askdirectory
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import serial.tools.list_ports
import threading
import csv



###################################################
#Stop bitid ja Serial uhenduse pean ule vaatama!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!11



start_logging = False
start = False
ser_out1 = None
ser_out2 = None

plot_x = []
plot_y =[]
plot_enabled = False


# Function to list available serial ports
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]
#####################################################################
# Initialize the serial ports based on selected ports
def initialize_serial(port_number,  port_baudrate, data_number):
    ser = None
    
    try:
        ser= serial.Serial(
            port=port_number,
            baudrate=port_baudrate,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_TWO,
            bytesize=serial.SEVENBITS,
            
        )

        if ser.is_open :
            print(f"Connected to {port_number}")
            data_number.config(text="Connected",background='green')
            read_button.config(bg='orange', state='active')
            
            
    except serial.SerialException or ValueError:
        print(f"Failed to connect to {port_number}")
        data_number.config(text="Connection Failed", background='red')
        read_button.config(bg='#3498db')
        ser = None

    return ser

#####################################################################

# Data cleaning and decodeing from unnecessary characters
def cleanData(serialIn, unit):
    try:
        raw_data = serialIn.readline()
        data_cleaning = raw_data.decode('utf-8').strip()
        if data_cleaning:  
            data_cleaning = ' '.join(data_cleaning.split())
            value = float(data_cleaning)/10.0
            if unit == 'N':
                value *= 9.80665
            elif unit == 'µm':
                value *= 1000
            return value
        else:
            return 0.0
    except ValueError:
        print("Failed data cleaning")
        
        return 0.0

#####################################################################   
def log_data():
    global start_time, start_logging  
    if start_logging:
        start_logging = False     
        log_button.config(text="Start Data Logging", bg='Green')
    else:
        start_logging = True
        start_time = time.time()
        log_button.config(text="Stop Data Loging", bg='yellow')





#####################################################################
# Start or stop reading data from serial ports
def start_reading():
    global start
    if start:
        start = False
        read_button.config(text="Start Read Serial", bg='Green')
        print("Stopped reading")
        
    else:
        start = True
        read_button.config(text="Stop Reading Serial", bg='Red')
        print("Started reading")

        #############################################################
        ##For running read loop in the background so GUI is usable###
        threading.Thread(target=read_loop, daemon=True).start() #####
        #############################################################



#####################################################################


# Loop to continuously read from the serial ports
def read_loop():
    global start, current_time, start_time, start_logging ,plot_x, plot_y
    
    start_time = time.time() 
    data_out1 = 0.0
    data_out2 = 0.0
    start_logging= 0
    elapsed_time = 0.0
    load_cell_unit = data_unit1.get()
    mm_unit = data_unit2.get()

    plot_y = []
    plot_x = []

    #################################################################
    #Main data reading loop
    while start:
        #Timestamp from the start of data reading
        current_time = time.time() * 1000
        
        if ser_out1 :
            data_out1 = cleanData(ser_out1,load_cell_unit)
            data1.config(text=f'{data_out1} {load_cell_unit}', background='#ecf0f1')
            
        if ser_out2:
            data_out2 = cleanData(ser_out2, mm_unit)
            data2.config(text=f'{data_out2} {mm_unit}', background='#ecf0f1')

        if (data_out1 or data_out2) and start_logging:
            last_time = elapsed_time 
            elapsed_time = current_time - (start_time * 1000) 
            elapsed_time= f'{elapsed_time:.0f}'

            timestamp.config(text=f'Time: {elapsed_time} ms')
            if last_time != elapsed_time:
                writeToFile(data_out1,data_out2,elapsed_time)
            
            plot_x.append(data_out1)
            plot_y.append(data_out2)


#####################################################################
# Function to connect to selected ports
def connect_ports():
    global ser_out1, ser_out2
    try:
        if ser_out1 and ser_out1.is_open:
            ser_out1.close()

        ser_out1 = initialize_serial(port_var1.get(), baudrate_var1.get(), data1)
    except ValueError:
        data1.config(text="Connection Failed", background='red')
        read_button.config(bg='#3498db')
         
    try:
        if ser_out2 and ser_out2.is_open:
            ser_out2.close()

        ser_out2 = initialize_serial(port_var2.get(), baudrate_var2.get(), data2)
    except ValueError:
        data2.config(text="Connection Failed", background='red')
        read_button.config(bg='#3498db')

    
 ####################################################################
 # Port refreshing       

def refresh_ports():
    ports = list_serial_ports()
    
    save_p1 = port_var1.get()
    save_p2 = port_var2.get()
    
    port_menu1['menu'].delete(0, 'end')
    port_menu2['menu'].delete(0, 'end')
    
    for port in ["None"] + ports:
        port_menu1['menu'].add_command(label=port, command=tk._setit(port_var1, port))
        port_menu2['menu'].add_command(label=port, command=tk._setit(port_var2, port))

    if save_p1 in ports:
        port_var1.set(save_p1)
    else:
        port_var1.set("Select Port 1")
        data1.config(text="",background='#ecf0f1')

    if save_p2 in ports:
        port_var2.set(save_p2)
    else:
        port_var2.set("Select Port 2")
        data2.config(text="",background='#ecf0f1')
    

#####################################################################
def select_directory():
    selected_dir = tk.filedialog.askdirectory()
    if selected_dir:
        save_directory.set(selected_dir)
        if save_directory.get()!= "Select Directory":
            log_button.config(state='active')

def writeToFile(d1, d2, ts):
    file_path = f"{save_directory.get()}/{file_name_var.get()}"
    with open(file_path, 'a') as file:
        w = csv.writer(file)
        w.writerow([d1, d2, ts])

######################################################################


    
def toggle_plot():
    global plot_enabled
    global plot_x, plot_y, plot_enabled
    plot_enabled = not plot_enabled
    plot_button.config(text="Hide Plot" if plot_enabled else "Show Plot")
    if plot_enabled:
        fig, ax = plt.subplots()
        ax.plot(plot_x, plot_y, label='Data Plot')
        ax.set_xlabel('X Data')
        ax.set_ylabel('Y Data')
        ax.set_title('Data Plot')
        ax.legend()

        # Embed the plot into the Tkinter window
        canvas = FigureCanvasTkAgg(fig, master=s)
        canvas.draw()
        canvas.get_tk_widget().grid(row=5, column=0, columnspan=3, pady=10)
    else:
        # Clear the plot if it's disabled
        for widget in s.grid_slaves(row=5):
            widget.grid_forget()
        plot_x = []
        plot_y = []





#####################################################################
# GUI Function
def GUI():

    global read_button,  data1, data2, timestamp, data_unit1, data_unit2
    global port_var1, port_var2, baudrate_var1, baudrate_var2, baudrate_menu1, baudrate_menu2, port_menu2, port_menu1
    global save_directory, file_name_var ,log_button, plot_button

    global s
    #################################################################
    #Tkinter initalizing
    s = tk.Tk()
    s.title("Deformation Test Bench Data Logger")
    s.geometry("1000x1000")
    s.config(bg='#ffffff')
    

    #################################################################
    #Save to Directory
    save_directory = tk.StringVar()
    save_directory.set("Select Directory")

    file_name_var = tk.StringVar()
    file_name_var.set("DataLog1.csv")  
    

    file_frame = tk.Frame(s, highlightbackground='black', highlightthickness=3, pady=2, padx=20)
    file_name_entry = tk.Entry(file_frame,
                                textvariable=file_name_var,
                                font=("Arial", 12, 'italic'), 
                                
                                width=20
                                )
    
    file_name_label = tk.Label(file_frame,
                               text="CSV File Name:",
                               font=("Arial", 10)
                               )
    

    

    
    
    #################################################################
    
    directory_label = tk.Label(file_frame,
                               textvariable=save_directory,
                               font=("Arial", 12, 'italic'),
                               bg='white',
                               fg='black',
                               width=18,
                               height=1, 
                               anchor='w',
                               relief='sunken'

                               )

    directory_button = tk.Button(file_frame,
                                text="...",
                                command=select_directory,
                                anchor='w', 
                                cursor="hand2",
                                font=("Arial", 10),
                                activebackground='#909497',
                                activeforeground='white',
                                highlightbackground='black',
                                border=3,
                                width=0,
                                height=1,
                                padx=6,
                                pady=0.0001
                                
                                )
    

    file_name_label.pack(side='top', padx=0, anchor='w')
    file_name_entry.pack(side='top', padx=0, anchor='w')
    directory_button.pack(side='right', padx=0, pady=2, anchor='w')
    directory_label.pack(side='left', padx=0, pady=0, anchor='w')

    #Port Frame
    #################################################################
    port_frame1 = tk.Frame(s,
                        bg='#ffffff',
                        highlightbackground='black',
                        highlightthickness=3                     
                        )
    port_frame2 = tk.Frame(s, 
                        bg='#ffffff',
                        highlightbackground='black',
                        highlightthickness=3
                        )
     
    # Dropdown for first port
    port_var1 = tk.StringVar()
    port_var1.set("Select Port 1")
    ports1 = ["None"] + list_serial_ports()
    port_menu1 = tk.OptionMenu(port_frame1, port_var1, *ports1)
    port_menu1.configure(padx=50,
                        pady=10,
                        width=11,
                        height=1, 
                        font=("Arial",12)
                        
                        )
    #################################################################

    # Dropdown for second port
    port_var2 = tk.StringVar()
    port_var2.set("Select Port 2")
    ports2 = ["None"] +list_serial_ports()
    port_menu2 = tk.OptionMenu(port_frame2, port_var2, *ports2)    
    port_menu2.configure(padx=50,
                        pady=10,
                        width=11, 
                        height=1, 
                        font=("Arial",12)
                        
                        )
    #################################################################
    rates = [9600, 19200, 38400, 57600,115200] 
    # Port1 baudrate
    baudrate_var1 = tk.StringVar()
    baudrate_var1.set("Select Baudrate")
    
    baudrate_menu1 = tk.OptionMenu(port_frame1, baudrate_var1, *rates)
    baudrate_menu1.configure(padx=50,
                            pady=10, 
                            width=11, 
                            height=1, 
                            font=("Arial",12)
                            )
    #################################################################
    # Port2 baudrate
    baudrate_var2 = tk.StringVar()
    baudrate_var2.set("Select Baudrate")
    
    baudrate_menu2 = tk.OptionMenu(port_frame2, baudrate_var2, *rates)
    baudrate_menu2.configure(padx=50,
                            pady=10, 
                            width=11, 
                            height=1, 
                            font=("Arial",12)
                            )
    #################################################################
    
    port_menu1.pack(side='top', padx=0, anchor='w')
    baudrate_menu1.pack(side='bottom', padx=0, anchor='w')
    
    port_menu2.pack(side='top', padx=0, anchor='w')
    baudrate_menu2.pack(side='bottom', padx=0, anchor='w')
    
    #################################################################
    # Connect button to initialize the ports
    connect_frame = tk.Frame(s, bg='#ffffff')
    connect_button = tk.Button(connect_frame, 
                               text="Connect to ports", 
                               command=connect_ports,
                               background="#229954",
                               activebackground='green',
                               activeforeground='white', 
                               fg="black",
                               cursor="hand2",
                               bd= 3,
                               font=("Arial", 12, 'bold'),
                               height=1, 
                               width=13)
    
    refresh_button = tk.Button(connect_frame, 
                               text="Refresh", 
                               command=refresh_ports,
                               background='#3498db',
                               activebackground='#1F618D',
                               activeforeground='white', 
                               fg="black",
                               cursor="hand2",
                               bd= 3,
                               anchor='w',
                               font=("Arial", 12, 'bold'),
                               height=1, 
                               width=6)
    
    connect_button.pack(side='top', padx=0, pady=0, anchor='w')
    refresh_button.pack(side='bottom', padx=1, pady=10, anchor='w')
    #################################################################
    # Button to start reading data
    read_button = tk.Button(s, 
                    text="Start Reading Serial", 
                    command=start_reading,
                    background='#3498db',
                    activebackground="#1F618D", 
                    activeforeground="white",
                    anchor="center",
                    bd=3,
                    cursor="hand2",
                    disabledforeground="gray",
                    fg="black",
                    font=("Arial", 16, 'bold'),
                    height=2,
                    highlightbackground="black",
                    highlightcolor="green",
                    highlightthickness=2,
                    justify="center",
                    state='disabled',
                    padx=10,
                    pady=5,
                    width=18)
    

    #################################################################
    plot_button = tk.Button(s, 
                        text="Show Plot", 
                        command=toggle_plot,
                        background='#3498db',
                        activebackground="#1F618D", 
                        activeforeground="white",
                        anchor="center",
                        bd=3,
                        cursor="hand2",
                        disabledforeground="gray",
                        fg="black",
                        font=("Arial", 16, 'bold'),
                        height=2,
                        highlightbackground="black",
                        highlightcolor="green",
                        highlightthickness=2,
                        justify="center",
                        padx=10,
                        pady=5,
                        width=18)
    #################################################################
    #Data logging 

    log_button = tk.Button(s, 
                    text="Log to File", 
                    command=log_data,
                    background='#3498db',
                    activebackground="#1F618D", 
                    activeforeground="white",
                    anchor="center",
                    bd=3,
                    cursor="hand2",
                    disabledforeground="gray",
                    fg="black",
                    font=("Arial", 16, 'bold'),
                    height=2,
                    highlightbackground="black",
                    highlightcolor="green",
                    highlightthickness=2,
                    justify="center",
                    
                    padx=10,
                    pady=5,
                    width=18,
                    
                    state='disabled'
                    )


    #################################################################
    d1_frame = tk.Frame(s, highlightbackground='black', highlightthickness=3)
    d2_frame = tk.Frame(s, highlightbackground='black', highlightthickness=3)   
    ts_frame = tk.Frame(s, highlightbackground='black', highlightthickness=3)
    # Data
    colorData = "#ecf0f1"
    data1 = tk.Label(d1_frame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    anchor='s',
                    font=("Arial", 20),
                    height=1, 
                    width=15)
    

    data2 = tk.Label(d2_frame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    font=("Arial", 20),
                    height=1, 
                    width=15)
    
    
    timestamp = tk.Label(ts_frame,
                    background=colorData,
                    fg="black",
                    bd= 6,
                    font=("Arial", 20),
                    height=1, 
                    width=15)
    #################################################################
    # Dropdown for units
    data_unit1 = tk.StringVar()
    data_unit1.set("kg")
    units1 = ['kg','N'] 
    units_menu1 = tk.OptionMenu(d1_frame, data_unit1, *units1)
    units_menu1.configure(padx=1,
                        pady=1,
                        width=3,
                        height=1, 
                        font=("Arial",12)
                        
                        )
    
    data_unit2 = tk.StringVar()
    data_unit2.set("mm")
    units2 = ['mm','µm'] 
    units_menu2 = tk.OptionMenu(d2_frame, data_unit2, *units2)
    units_menu2.configure(padx=1,
                        pady=1,
                        width=3,
                        height=1, 
                        font=("Arial",12)
                        
                        )
    #################################################################
    colorLable='#3498DB'
    data_lable1 = tk.Label(d1_frame,
                    text="Load cell",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    font=("Arial", 12,'bold'),
                    height=1, 
                    width=18)
    
    data_lable2 = tk.Label(d2_frame,
                    text="mm",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    font=("Arial", 12, 'bold'),
                    height=1, 
                    width=18)

    time_lable1 = tk.Label(ts_frame,
                    text="Timestamp",
                    background=colorLable,
                    fg="black",
                    anchor='center',
                    bd= 6,
                    font=("Arial", 12,'bold'),
                    height=1, 
                    width=25)
    
    #################################################################
    data1.pack(side='bottom', padx=0, pady=0)
    data_lable1.pack(side='left', padx=0, pady=0)
    units_menu1.pack(side='right',padx=0,pady=0)
    

    data2.pack(side='bottom', padx=0, pady=0)
    data_lable2.pack(side='left', padx=0, pady=0)
    units_menu2.pack(side='right',padx=0,pady=0)
    
    timestamp.pack(side='bottom', padx=0, pady=0)
    time_lable1.pack(side='top', padx=0, pady=0)

##################################################################### 
#GRID
    port_frame1.grid(row=0, column=0, pady=5, padx=10, sticky='w')
    port_frame2.grid(row=0, column=1, padx=10, pady=5, sticky='w')
    connect_frame.grid(row=0, column=2, pady=5, padx=10, sticky='w')

    d1_frame.grid(row=2, column=0, pady=10, padx=10, sticky='w')
    d2_frame.grid(row=2, column=1, pady=10, padx=10, sticky='w')
    ts_frame.grid(row=2, column=2, pady=10, padx=10, sticky='w')

    read_button.grid(row=3, column=0, pady=20, padx=10, sticky='w')
    log_button.grid(row=3, column=2, pady=20, padx=10, sticky='w')
    file_frame.grid(row=3, column=1, pady=20, padx=10, sticky='w')
    plot_button.grid(row=4, column=0, pady=20, padx=10, sticky='w')

    s.mainloop()



if __name__ == "__main__":
    GUI()


#####################################################################