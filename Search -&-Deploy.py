import customtkinter as ctk
from customtkinter import filedialog
import os
import shutil
import json
from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox
import sys
import subprocess

# We store all of our userinputs in the config file
config_file = 'config.cfg'

# Variables for creating a shortcut
program_path = os.path.dirname(__file__)
startup_folder = os.path.join(os.getenv('APPDATA'),'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup')
shortcut_file = os.path.join(program_path, 'Search & Deploy.lnk')

# We need some counters
files_transferred = 0
# get the user machines total number of logical cores
thread_count = os.cpu_count()
text_pattern = []

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
        os.remove(os.path.join(startup_folder, 'Search & Deploy.lnk'))

# Transfer the file from source to destination if it doesn't exist
# or if the source file modified time is greater than the destination files
def transfer_file(source_file, dest_file):
    global files_transferred
    if not os.path.exists(dest_file):
        shutil.copy2(source_file, dest_file)
        files_transferred += 1
        #output_textbox.insert("end", f"Copied new file: {source_file} to {dest_file}")
        print(f"Copied new file: {source_file} to {dest_file}")
    else:
        source_modified = os.path.getmtime(source_file)
        dest_modified = os.path.getmtime(dest_file)

        if source_modified > dest_modified:
            shutil.copy2(source_file, dest_file)
            files_transferred += 1
            #output_textbox.insert("end", f"Updated file: {source_file} to {dest_file}")
            print(f"Updated file: {source_file} to {dest_file}")

# Transfer the files from the source directory if they match the pattern criteria
def process_files(root, files, dest_path):
    global text_pattern
    for file in files:
        for pattern in text_pattern:
            if pattern in file:
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
    #print(search_criteria_var.get())

    # Split the search criteria to the list, removing spaces
    no_space_pattern = search_criteria_var.get().replace(' ','')
    split_patterns = no_space_pattern.split(',')
    text_pattern.extend(split_patterns)
    print(f"Text Pattern: {text_pattern}")
    print(f"Thread Count: {thread_count}")

    if toggle_update_svn:
        svn_command = f"svn update {source_dir}"
        print(svn_command)
        #subprocess.run(svn_command)

    if not os.path.isdir(source_dir):
        messagebox.showerror("Error", "Source directory does not exist.")
        return

    if not os.path.isdir(dest_dir):
        messagebox.showerror("Error", "Destination directory does not exist.")
        return

    # Start processing files
    start_transfer(source_dir, dest_dir)
    global files_transferred
    show_popup(files_transferred)
    #messagebox.showinfo("Success", f"File transfer completed!\n{files_transferred} files transferred.")
    files_transferred = 0
    text_pattern.remove(search_criteria_var.get())

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


def toggle_update_svn():
    config['UpdateSVN'] = update_svn_var.get()
    save_config(config)
    

# If the Config file exists, is populated, and the Startup Checkbox is True
def run_silently():
    source_dir = config.get('SourceDirectory')
    dest_dir = config.get('DestinationDirectory')
    
    if os.path.isdir(source_dir) and os.path.isdir(dest_dir):
        start_transfer(source_dir, dest_dir)
        # Display the Progress popup window
        show_popup(files_transferred)
        #messagebox.showinfo("Success", f"File transfer completed!\n{files_transferred} files transferred.\n{shortcut_file}")
    app.destroy()

"""
Custom Popup Window starts here

"""

def show_popup(files_transferred):
    # Create a new toplevel window (popup)
    popup = ctk.CTkToplevel()
    popup.title("Files Transferred")

    # Take the current status of the checkbox, update the config,
    # and create or delete the startup shortcut
    def toggle_startup():
        config['Startup'] = startup_var.get()
        save_config(config)
    
        if startup_var.get():
            shutil.copy2(shortcut_file, startup_folder)
        else:
            delete_shortcut()

    # Get the App Coordinates and lock in geometry
    popup.minsize(popup.winfo_width(), popup.winfo_height())
    popup_x_cordinate = int((popup.winfo_screenwidth() / 2) - (popup.winfo_width() / 2))
    popup_y_cordinate = int((popup.winfo_screenheight() / 2) - (popup.winfo_height() / 2))
    popup.geometry("+{}+{}".format(popup_x_cordinate, popup_y_cordinate-20))
    popup.resizable(False, False)
    
    # Popup Frame
    popup_frame = ctk.CTkFrame(popup)
    popup_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Labels to display file transfer results
    message_label = ctk.CTkLabel(popup_frame, text=f"File transfer completed!\n{files_transferred} files transferred.")
    message_label.pack(pady=30)
    
    startup_var = ctk.BooleanVar(value=config.get('Startup', False))
    startup_toggle = ctk.CTkCheckBox(popup, text="Run on startup", variable=startup_var, command=toggle_startup).pack(side="left", pady=12,padx=10)
    # OK button to close the popup
    ok_button = ctk.CTkButton(popup, text="OK", command=popup.destroy)
    ok_button.pack(side="right", pady=10)

    popup.focus_set()
    popup.grab_set()

    def close_popup(popup, textbox):
        popup.destroy()  # Close the popup window
        global files_transferred
        #files_transferred = 0
        #app.focus_set()  # Give focus back to the textbox


"""
Start of Main App GUI begins here
"""

# Load the configuration
config = load_config()

app = ctk.CTk()
app.title("Search & Deploy - File Sorting Tool")
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

# Get the App Coordinates and lock in geometry
app.update()
app.minsize(app.winfo_width(), app.winfo_height())
x_cordinate = int((app.winfo_screenwidth() / 2) - (app.winfo_width() / 2))
y_cordinate = int((app.winfo_screenheight() / 2) - (app.winfo_height() / 2))
app.geometry("+{}+{}".format(x_cordinate, y_cordinate-20))
app.resizable(False, False)

for index in [0, 1, 2]:
    app.columnconfigure(index=index, weight=1)
    app.rowconfigure(index=index, weight=1)

# Create Frames
widget_frame = ctk.CTkFrame(app)
toggle_frame = ctk.CTkFrame(app)
widget_frame.pack(fill="both", expand=True, padx=10, pady=10)
toggle_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Source Directory
source_path_var = ctk.StringVar(value=config.get('SourceDirectory', ''))
source_label = ctk.CTkLabel(widget_frame, text="Source Directory:").grid(pady=12,padx=10,column=0,row=0,sticky='w')
source_entry = ctk.CTkEntry(widget_frame, textvariable=source_path_var, width=300).grid(pady=12,padx=10,column=1,row=0,sticky='ew')
source_button = ctk.CTkButton(widget_frame, text="Select Source", command=select_source).grid(pady=12,padx=10,column=2,row=0,sticky='e')

# Destination Directory
destination_path_var = ctk.StringVar(value=config.get('DestinationDirectory', ''))
destin_label = ctk.CTkLabel(widget_frame, text="Destination Directory:").grid(pady=12,padx=10,column=0,row=1,sticky='w')
destin_entry = ctk.CTkEntry(widget_frame, textvariable=destination_path_var, width=300).grid(pady=12,padx=10,column=1,row=1,sticky='ew')
destin_button = ctk.CTkButton(widget_frame, text="Select Destination", command=select_destination).grid(pady=12,padx=10,column=2,row=1,sticky='e')

# Search Criteria
search_criteria_var = ctk.StringVar(value=config.get('SearchCriteria', ''))
criteria_label = ctk.CTkLabel(widget_frame, text="Search Criteria:").grid(pady=12,padx=10,column=0,row=2,sticky='w')
criteria_entry = ctk.CTkEntry(widget_frame, textvariable=search_criteria_var, width=300).grid(pady=12,padx=10,column=1,row=2,sticky='ew')
# Start Transfer Button
transfer_button = ctk.CTkButton(widget_frame, text="Start Transfer", command=validate_and_start).grid(pady=12,padx=10,column=2,row=2,sticky='e')

#output_textbox = ctk.CTkTextbox(widget_frame, wrap=ctk.WORD, width=600)
#output_textbox.grid(pady=12, padx=10, columnspan=3, sticky='nsew')
# sys.stdout = TextRedirector(output_textbox)

# Define Checkbox values
startup_var = ctk.BooleanVar(value=config.get('Startup', False))
# startup_toggle = ctk.CTkCheckBox(toggle_frame, text="Run on startup", variable=startup_var, command=toggle_startup).grid(pady=12,padx=10,column=0,row=4,sticky='w')
update_svn_var = ctk.BooleanVar(value=config.get('Startup', False))
update_svn_toggle = ctk.CTkCheckBox(toggle_frame, text="Update SVN", variable=update_svn_var, command=toggle_update_svn).grid(pady=12,padx=10,column=0,row=4,sticky='w')

# If the config indicates to run silently at startup
if config.get('Startup', False):
    app.iconify()
    run_silently()

# Save settings on exit
def on_exit():
    config['SourceDirectory'] = source_path_var.get()
    config['DestinationDirectory'] = destination_path_var.get()
    config['SearchCriteria'] = search_criteria_var.get()
    config['UpdateSVN'] = update_svn_var.get()
    config['Startup'] = startup_var.get()
    save_config(config)
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_exit)
app.mainloop()
