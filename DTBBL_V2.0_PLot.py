import tkinter as tk
from tkinter.filedialog import askdirectory
import multiprocessing
import queue
import serial
import serial.tools.list_ports
import csv
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import matplotlib.pyplot as plt
from collections import deque

#############################################################################################
## M2rkused ##
##############
#
#
#
#
#############################################################################################
data1_out = 0.0
data2_out = 0.0

#data1_offset = 0.0
data2_offset = 0.0

x_data = deque([0.0,0.0])
y_data = deque([0.0,0.0])


interval_time = 0.0
x_max = 10
x_min = -10
y_max = 5
y_min = -5

start_time = 0
start_logging = False
start = False
processes = []  


#####################################################################
def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [port.device for port in ports]


#####################################################################
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
def read_serial_data(port, baudrate, queue):
    data = 0.0
    try:
        with serial.Serial(port, baudrate, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS) as ser:
            while True:
                if ser.in_waiting > 0:
                    try:
                        data = ser.readline().decode('utf-8').strip()
                        value = float(data)
                        queue.put(value)
                    except ValueError:
                        print(f"Received invalid data: {data}")
                        continue
    except Exception as e:
        print(e)
        queue.put(f"Error: {e}")


#####################################################################
def log_data():
    global start_time, start_logging, interval_time
    if start_logging:
        start_logging = False     
        log_button.config(text="Start Data Logging", bg='Green')
    else:
        start_logging = True
        start_time = time.time()
        interval_time = time.time()
        log_button.config(text="Stop Data Loging", bg='yellow')


#####################################################################
def zero_point():
    global data1_offset, data2_offset
    global x_max, x_min, y_max, y_min
    try:
        #data1_offset = queue1.get(timeout=0.01)
        data2_offset = queue2.get(timeout=0.01)

            # Reset the plot data
        x_data.clear()
        y_data.clear()

        x_data.append(0.0)
        y_data.append(0.0)

        y_max = 0.01
        y_min = -0.01  

        ax.clear()
        canvas.draw()
        
        
    except queue.Empty:
        data2_offset = 0.0
        print("offset is already at zero")
    
    
#####################################################################
def toggle_reading(queue1, queue2):
    global start,start_logging, processes, read_button
    global start_time, elapsed_time
    if start:
        start = False
        start_logging = False
        for p in processes:
            p.terminate()
        processes = []
        read_button.config(text="Start Reading Serial", bg='#3498db')
        log_button.config(text="Log to File", bg='#3498db')
        print("Stopped reading")
        
    else:
        start = True
        start_time =time.time()
        elapsed_time = 0.0
        print("Started reading")
        #############################################################
        try:
            port1 = port_var1.get()
            if port1 != 'None':
                baudrate1 = int(baudrate_var1.get())
                p1 = multiprocessing.Process(target=read_serial_data, args=(port1, baudrate1, queue1))
                p1.start()
                processes.append(p1)
        except ValueError as e:
            read_button.config(text="Start Reading Serial", bg='#3498db')
            print("Port or Baudrate not selected: ", e)
        #############################################################    
        try:
            port2 = port_var2.get()
            if port2 != "None":
                baudrate2 = int(baudrate_var2.get())
                p2 = multiprocessing.Process(target=read_serial_data, args=(port2, baudrate2, queue2))
                p2.start()
                processes.append(p2)
        except ValueError as e:
            read_button.config(text="Start Reading Serial", bg='#3498db')
            print("Port or Baudrate not selected: ", e)

        #############################################################
        read_button.config(text="Stop Reading Serial", bg='Red')
        
            
#####################################################################
def update_labels(queue1, queue2):
    global start_time, elapsed_time, start_logging, data1_out, data2_out

    while not queue1.empty() or not queue2.empty():
        current_time = time.time() * 1000
        try:
           ##########################################################
            if not queue1.empty():
                data1_out = queue1.get(timeout=0.01)
                if isinstance(data1_out, (int, float)):
                    #data1_out -= data1_offset  
                    if data_unit1.get() == 'kg':
                        data1_out *= 0.1
                        data1_out = round(data1_out , 4)
                    elif data_unit1.get() == 'N':
                        data1_out *= 9.80665
                        data1_out = round(data1_out, 4)
                    data1.config(text=f'{data1_out} {data_unit1.get()}')
            #########################################################
            if not queue2.empty():
                data2_out = queue2.get(timeout=0.01)
                if isinstance(data2_out, (int, float)):
                    data2_out -= data2_offset 
                    if data_unit2.get() == 'mm':
                        data2_out = round(data2_out , 2)
                    elif data_unit2.get() == 'µm':
                        data2_out *= 1000
                        data2_out = round(data2_out, 2)
                    data2.config(text=f'{data2_out} {data_unit2.get()}')

            #########################################################
            last_time = elapsed_time
            elapsed_time = current_time - (start_time * 1000)
            elapsed_time = f'{elapsed_time:.0f}'
            timestamp.config(text=f'{elapsed_time} ms')
            #########################################################

            if start_logging and last_time != elapsed_time:
                writeToFile(data1_out, data2_out, elapsed_time)
            #########################################################
            
            x_data.append(data1_out)    
            y_data.append(data2_out)    


        except queue.Empty:
            break
    root.after(1, update_labels, queue1, queue2)


def update_plot():
    global x_max, x_min, y_max, y_min, start_time, interval_time
    current_time = time.time()

    ax.clear()  
   
    #if current_time > (interval_time + 0.1) and start:
    #    interval_time = time.time()
    #    x_data.append(data1_out)
    #    y_data.append(data2_out)

    
        
    
    if x_max < x_data[-1]:
        x_max = x_data[-1]
    elif x_min > x_data[-1]:
        x_min = x_data[-1]

    if y_max < y_data[-1]:
        y_max = y_data[-1]
    elif y_min > y_data[-1]:
        y_min = y_data[-1]
   

    ax.plot(x_data, y_data)  # Plot the new data
    ax.set_xbound(x_min,x_max)
    ax.set_ybound(y_min,y_max) 
    ax.set_xlabel("Load Cell")
    ax.set_ylabel("Displacement")
    ax.set_title("Plot")
    ax.grid(True)

    

    canvas.draw()  # Redraw the canvas

    root.after(10, update_plot)      # Schedule the next update





#####################################################################
def select_directory():
    selected_dir = tk.filedialog.askdirectory()
    if selected_dir:
        save_directory.set(selected_dir)
        if save_directory.get()!= "Select Directory":
            log_button.config(state='active')


#####################################################################
def writeToFile(d1, d2, ts):
    file_path = f"{save_directory.get()}/{file_name_var.get()}"
    with open(file_path, 'a', newline='') as file:
        w = csv.writer(file)
        w.writerow([d1, d2, ts])




#####################################################################
def create_gui(queue1, queue2):
    global root
    global ax, canvas
    global save_directory, file_name_var ,log_button
    global read_button,  data1, data2, timestamp, data_unit1, data_unit2
    global port_var1, port_var2, baudrate_var1, baudrate_var2, baudrate_menu1, baudrate_menu2, port_menu2, port_menu1
    
    #####################################################################
    root = tk.Tk()
    root.title("Deformation Test Bench Data Logger")
    root.geometry("1400x600")
    root.config(bg='#ffffff')
    
    fig = Figure(figsize=(5,4), dpi=100)
    ax = fig.add_subplot(111)
    ax.set_xlabel("Load Cell")
    ax.set_ylabel("Displacement")
    ax.set_title("Plot")
    ax.grid(True)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().grid(row=0, column=3, rowspan=5, padx=10, pady=10)
    canvas.draw()



    #################################################################
    read_button = tk.Button(root, 
                    text="Start Reading Serial", 
                    command=lambda: toggle_reading(queue1, queue2),
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
    refresh_button = tk.Button(root, 
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
    
    #################################################################
    zero_button = tk.Button(root, 
                    text="Zero value", 
                    command=zero_point,
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
    #Save to Directory
    save_directory = tk.StringVar()
    save_directory.set("Select Directory")

    file_name_var = tk.StringVar()
    file_name_var.set("DataLog1.csv")  
    
    file_frame = tk.Frame(root, highlightbackground='black', highlightthickness=3, pady=2, padx=20)
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
    
    #################################################################
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
    
    #################################################################
    log_button = tk.Button(root, 
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
    port_frame1 = tk.Frame(root,
                        bg='#ffffff',
                        highlightbackground='black',
                        highlightthickness=3                     
                        )
    port_frame2 = tk.Frame(root, 
                        bg='#ffffff',
                        highlightbackground='black',
                        highlightthickness=3
                        )
     
    #####################################################################
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
    d1_frame = tk.Frame(root, highlightbackground='black', highlightthickness=3)
    d2_frame = tk.Frame(root, highlightbackground='black', highlightthickness=3)   
    ts_frame = tk.Frame(root, highlightbackground='black', highlightthickness=3)

    #####################################################################
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

    port_menu1.pack(side='top', padx=0, anchor='w')
    baudrate_menu1.pack(side='bottom', padx=0, anchor='w')
    
    port_menu2.pack(side='top', padx=0, anchor='w')
    baudrate_menu2.pack(side='bottom', padx=0, anchor='w')
    
    file_name_label.pack(side='top', padx=0, anchor='w')
    file_name_entry.pack(side='top', padx=0, anchor='w')
    directory_button.pack(side='right', padx=0, pady=2, anchor='w')
    directory_label.pack(side='left', padx=0, pady=0, anchor='w')

    #################################################################
    port_frame1.grid(row=0, column=0, pady=5, padx=10, sticky='w')
    port_frame2.grid(row=0, column=1, padx=10, pady=5, sticky='w')
    refresh_button.grid(row=0, column=2, pady=20, padx=10, sticky='w')

    d1_frame.grid(row=2, column=0, pady=10, padx=10, sticky='w')
    d2_frame.grid(row=2, column=1, pady=10, padx=10, sticky='w')
    ts_frame.grid(row=2, column=2, pady=10, padx=10, sticky='w')
    
    read_button.grid(row=3, column=0, pady=20, padx=10, sticky='w')
    zero_button.grid(row=3, column=1, pady=20, padx=10, sticky='w')
    log_button.grid(row=4, column=0, pady=20, padx=10, sticky='w')
    file_frame.grid(row=4, column=1, pady=20, padx=10, sticky='w')

    #####################################################################
    root.protocol('WM_DELETE_WINDOW', cleanup_and_close)

    root.after(1, update_labels, queue1, queue2)
    root.after(10, update_plot)  # Schedule the first plot update

    root.mainloop()

#####################################################################
def cleanup():
    global processes
    for p in processes:
        p.terminate()
    processes = []

#####################################################################
def cleanup_and_close():
    cleanup()
    root.destroy()


#####################################################################
if __name__ == "__main__":
    multiprocessing.freeze_support()
    queue1 = multiprocessing.Queue()
    queue2 = multiprocessing.Queue()

    create_gui(queue1, queue2)
