"""
File that contains helper functions
Written by M. Ronde's team
"""
import os
import glob
import matplotlib.pyplot as plt

from tkinter import Tk, filedialog


def get_all_edf_files(root_dir):
    """
    Finds all .edf files. Works for edf files located in the root of the path, but
    also for all nested edf files. Skips the 'trash_recordings' folder.

    Parameters:
    ### root_dir [str]: Root folder to search for EDF files.

    Returns:
    ### edf_files [list]: List of paths to all EDF files found
    """
    edf_files = []

    # Walk through root directory and all subdirectories
    for root, dirs, files in os.walk(root_dir):
        # do not handle recordings that are in trash folder
        if "trash_recordings" in dirs:  
            dirs.remove("trash_recordings")
        
        # Add all EDF files in the current folder
        edf_files.extend(glob.glob(os.path.join(root, '*.edf')))
    
    return edf_files


def create_dir_if_not_exists(directory):
    """
    Create a directory if it does not already exist.

    Parameters:
    ### directory [str]: Path to the directory that should be created

    Returns:
    ### None: The function creates the directory if needed
    """
    if not os.path.exists(directory):
        os.makedirs(directory)


def save_figure(path, bbox_inches='tight', dpi=300):
    """
    Custom function that lets you save a figure and creates the directory where necessary

    Parameters:
    ### path [str]: Full path where the figure should be saved, including filename.
    ### bbox_inches [str]: Bounding-box option passed to plt.savefig().
        Default is "tight".
    ### dpi [int]: Figure resolution in dots per inch. Default is 300.

    Returns:
    ### None: The function saves the current figure to the selected path.
    """
    # If no folder is specified, assume the current folder. (ADDED)
    # Split path into directory and filename
    directory, filename = os.path.split(path)
    if directory == '':
        directory = '.'

    # If directory does not exist yet, create it
    if not os.path.exists(directory):
        os.makedirs(directory)

    save_path = os.path.join(directory, filename)

    # Actually save the figure
    plt.savefig(save_path, bbox_inches=bbox_inches, dpi=dpi)


# Tkinter functions used to request file/folder locations from the user

def select_folder(title):
    """
    Open a dialog window for selecting an existing folder.

    Parameters:
    ### title [str]: Title shown at the top of the folder-selection dialog.

    Returns:
    ### folder_path [str]: Path to the selected folder.
    """
    root = Tk()
    root.withdraw()

    return filedialog.askdirectory(title=title)


def select_file(title, filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))):
    """
    Open a dialog window for selecting a file.

    Parameters:
    ### title [str]: Title shown at the top of the file-selection dialog.
    ### filetypes [tuple]: File type filters shown in the dialog.
        Default allows Excel files and all files.

    Returns:
    ### file_path [str]: Path to the selected file
    """
    root = Tk()
    root.withdraw()

    return filedialog.askopenfilename(
        title=title,
        filetypes=filetypes
    )


def get_save_path(title, filetypes=(("Excel files", "*.xlsx"), ("All files", "*.*"))):
    """
    Open a dialog window for choosing where to save a file.

    Parameters:
    ### title [str]: Title shown at the top of the save-file dialog.
    ### filetypes [tuple]: File type filters shown in the dialog.
        Default allows Excel files and all files.

    Returns:
    ### save_path [str]: Path selected for saving the file.
    """
    root = Tk()
    root.withdraw()

    return filedialog.asksaveasfilename(
        title=title,
        defaultextension=".xlsx",
        filetypes=filetypes
    )


def select_or_create_folder(title):
    """
    Open a dialog window for selecting or creating a folder.

    Parameters:
    ### title [str]: Title shown at the top of the folder-selection dialog.

    Returns:
    ### folder_path [str]: Path to the selected or newly created folder.
    """
    root = Tk()
    root.withdraw()  # Hide the main window

    # Prompt user to select an existing folder or create a new one
    return filedialog.askdirectory(
        title=title,
        mustexist=False
    )