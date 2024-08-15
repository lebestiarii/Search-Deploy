import customtkinter as ctk
from customtkinter import filedialog
import os
import shutil
import json
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
import sys

# We store all of our userinputs in the config file
config_file = 'config.cfg'

# Variables for creating a shortcut
program_path = os.path.dirname(__file__)
startup_folder = os.path.join(os.getenv('APPDATA'),'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
shortcut_file = os.path.join(program_path, 'Extract Job Copier.lnk')
# We need a file counter
files_transferred = 0
thread_count = 4

# Load the JSON formatted config file and 
def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            return json.load(file)
    return {}

# Save our configuration into the JSON file
def save_config(config):
    with open(config_file, 'w') as file:
        json.dump(config, file, indent=4)
    

# Delete the shortcut file when the Startup checkbox is unchecked
def delete_shortcut():
    if os.path.exists(shortcut_file):
        os.remove(os.path.join(startup_folder, 'Extract Job Copier.lnk'))

# Transfer the file from source to destination if it doesn't exist
# or if the source file modified time is greater than the destination files
def transfer_file(source_file, dest_file):
    if not os.path.exists(dest_file):
        shutil.copy2(source_file, dest_file)
        files_transferred += 1
        print(f"Copied new file: {source_file} to {dest_file}")
    else:
        source_modified = os.path.getmtime(source_file)
        dest_modified = os.path.getmtime(dest_file)

        if source_modified > dest_modified:
            shutil.copy2(source_file, dest_file)
            files_transferred += 1
            print(f"Updated file: {source_file} to {dest_file}")

# Transfer the files from the source directory if they match the pattern criteria
def process_files(root, files, dest_path):
    for file in files:
        if "SPCA" in file or "SPCB" in file:
            source_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, file)
            transfer_file(source_file, dest_file)

# Transfer files from source to destination using up to four threadworkers
def start_transfer(source_path, dest_path):
    files_transferred = 0
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        for root, dirs, files in os.walk(source_path):
            executor.submit(process_files, root, files, dest_path)


# Validate whether the selected file paths actually exist
def validate_and_start():
    source_dir = source_path_var.get()
    dest_dir = destination_path_var.get()

    if not os.path.isdir(source_dir):
        messagebox.showerror("Error", "Source directory does not exist.")
        return

    if not os.path.isdir(dest_dir):
        messagebox.showerror("Error", "Destination directory does not exist.")
        return

    # Start processing files
    start_transfer(source_dir, dest_dir)
    messagebox.showinfo("Success", f"File transfer completed!\n{files_transferred} files transferred.")


# Get your user inputs for source, destination, and startup configs
def select_source():
    #dialog = ctk.CTkFileDialog()
    path = filedialog.askdirectory(title="Select Source Directory")
    if path:
        source_path_var.set(path)

def select_destination():
    #dialog = ctk.CTkFileDialog()
    path = filedialog.askdirectory(title="Select Destination Directory")
    if path:
        destination_path_var.set(path)


# Take the current status of the checkbox, update the config,
# and create or delete the startup shortcut
def toggle_startup():
    config['Startup'] = startup_var.get()
    save_config(config)
    
    if startup_var.get():
        shutil.copy2(shortcut_file, startup_folder)
    else:
        delete_shortcut()

# If the Config file exists, is populated, and the Startup Checkbox is True
def run_silently():
    source_dir = config.get('SourceDirectory')
    dest_dir = config.get('DestinationDirectory')
    
    if os.path.isdir(source_dir) and os.path.isdir(dest_dir):
        start_transfer(source_dir, dest_dir)
        messagebox.showinfo("Success", f"File transfer completed!\n{files_transferred} files transferred.\n{shortcut_file}")
    sys.exit()

# Load the configuration
config = load_config()

# If the config indicates to run silently at startup
if config.get('Startup', False):
    run_silently()



# Start of the GUI
app = ctk.CTk()
app.title("File Transfer Tool")
app.geometry("480x160")

# Make the grid adjust to the window
#app.grid_rowconfigure(0, weight=1)
#app.grid_columnconfigure(0, weight=1)

# Source Directory
source_path_var = ctk.StringVar(value=config.get('SourceDirectory', ''))
ctk.CTkLabel(app, text="Source Directory:").grid(pady=12,padx=10,column=0,row=0,sticky='w')
ctk.CTkEntry(app, textvariable=source_path_var).grid(pady=12,padx=10,column=1,row=0,sticky='ew')
ctk.CTkButton(app, text="Select Source", command=select_source).grid(pady=12,padx=10,column=2,row=0,sticky='e')

# Destination Directory
destination_path_var = ctk.StringVar(value=config.get('DestinationDirectory', ''))
ctk.CTkLabel(app, text="Destination Directory:").grid(pady=12,padx=10,column=0,row=1,sticky='w')
ctk.CTkEntry(app, textvariable=destination_path_var).grid(pady=12,padx=10,column=1,row=1,sticky='ew')
ctk.CTkButton(app, text="Select Destination", command=select_destination).grid(pady=12,padx=10,column=2,row=1,sticky='e')

# Run Silently at Startup Checkbox
startup_var = ctk.BooleanVar(value=config.get('Startup', False))
ctk.CTkCheckBox(app, text="Run on startup", variable=startup_var, command=toggle_startup).grid(pady=12,padx=10,column=0,row=4,sticky='w')

# Start Transfer Button
ctk.CTkButton(app, text="Start Transfer", command=validate_and_start).grid(pady=12,padx=10,column=2,row=4,sticky='e')

# Save settings on exit
def on_exit():
    config['SourceDirectory'] = source_path_var.get()
    config['DestinationDirectory'] = destination_path_var.get()
    config['Startup'] = startup_var.get()
    save_config(config)
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_exit)
app.mainloop()
