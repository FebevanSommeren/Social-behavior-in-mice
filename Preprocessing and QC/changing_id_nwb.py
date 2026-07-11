"""
Update incorrect subject metadata in an NWB file.

This script is used for the special case where the NWB file contains an
incorrect subject_id and description. It creates a backup copy of the original
file, edits the subject metadata in place, and then verifies the updated subject
information using PyNWB.

The default example in main() updates the file
"3C_sociability_b2c4.3 (1).nwb" so that both subject_id and description are set
to "b2c4.3".

"""
from pynwb import NWBHDF5IO
import shutil
import h5py

def update_nwb_subject_id(
    nwb_path,
    new_subject_id,
    backup_suffix="_backup2",
):
    """
    Update the subject ID and subject description in an NWB file.

    This function creates a backup copy of the original NWB file, opens the
    original file with h5py, updates the subject_id and description fields, and
    then verifies the change using PyNWB.

    Parameters:
    ### nwb_path [str]: Path to the NWB file that should be edited.
    ### new_subject_id [str]: Correct subject ID to write into the NWB file.
    ### backup_suffix [str]: Suffix added to the backup filename.
        Default is "_backup2".

    Returns:
    #### backup_path [str]: Path to the backup file that was created.
    """

    # Create backup filename.
    backup_path = nwb_path.replace(".nwb", f"{backup_suffix}.nwb")

    # Save a backup copy before editing the NWB file.
    shutil.copy2(nwb_path, backup_path)
    print("Backup saved to:", backup_path)

    # Open the NWB file directly with h5py so subject metadata can be edited.
    with h5py.File(nwb_path, "r+") as f:
        subj = f["general"]["subject"]

        print("OLD subject_id:", subj["subject_id"][()].decode())
        print("OLD description:", subj["description"][()].decode())

        # Update subject_id and description.
        subj["subject_id"][()] = new_subject_id.encode()
        subj["description"][()] = new_subject_id.encode()

        print("NEW subject_id:", subj["subject_id"][()].decode())
        print("NEW description:", subj["description"][()].decode())

    # Verify the edited file using PyNWB.
    with NWBHDF5IO(nwb_path, "r") as io:
        nwb = io.read()
        print(nwb.subject)

    return backup_path

def main():
    """
    Run the subject-ID correction for the b2c4.3 NWB file.

    This main function applies update_nwb_subject_id() to the NWB file that has
    the incorrect subject metadata. It updates both the subject_id and
    description fields to "b2c4.3" and creates a backup before editing.

    Returns:
    ### None: The function edits the NWB file in place and prints the backup path
    """
    backup_path = update_nwb_subject_id(
        nwb_path="3C_sociability_b2c4.3 (1).nwb",
        new_subject_id="b2c4.3",
    )
    print("Backup path:", backup_path)

if __name__ == "__main__":
    main()