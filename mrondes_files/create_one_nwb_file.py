"""
Filter EEG data and create NWB files
Edited so that it runs for 1 file

This script converts one subject's EEG recording from EDF format into a Neurodata
Without Borders (NWB) file. It also adds subject metadata, electrode metadata,
raw EEG, filtered EEG, and TTL synchronization events.

The script is adapted from the shared NWB creation workflow, but is edited to run
for one EDF file at a time. This was useful, because, for most subjects, there
was already an NWB file available, so it was only necessary to create these 
files for certain subjects. 

Run from the project root with:
    python -m mrondes_files.create_nwb_files_2

"""
## Run this in the terminal: python -m shared.create_nwb_files

import re
import sys
import mne
import numpy as np
import pandas as pd
import os


from datetime import datetime
from dateutil import tz
from pynwb import NWBFile, NWBHDF5IO
from pynwb.file import Subject
from pynwb.ecephys import ElectricalSeries
from ndx_events import TTLs
from hdmf.backends.hdf5.h5_utils import H5DataIO

from helper_functions import *
from eeg_filter_functions import filter_eeg
from settings_general import *


def create_nwb_file(metadata, experiment_name):
    """
    Create the initial NWBFile object.

    This function creates the NWB file structure and adds general session
    information, such as the experiment name, session start time, institution,
    lab, experimenter, session ID, and arena information. Electrode and EEG data
    are added later by separate functions.

    Parameters:
    ### metadata [dict]: Metadata extracted from the EDF filename and behavior Excel file.
    ### experiment_name [str]: Name of the experiment, for example '3c_sociability'.

    Returns:
    ### nwb [pynwb.NWBFile]: Initial NWB file object without EEG or electrode data.
    """
    # load some project information from the settings_general.py file
    experimenter = general['experimenter']
    institution = general['institution']
    lab = general['lab']

    # prepare some metadata
    session_description = f'Animal {metadata["mouseId"]} in {experiment_name} experiment'
    start_time = datetime.strptime(
        '-'.join([metadata['date'], metadata['time']]),
        '%Y-%m-%d-%H-%M'
    ).replace(tzinfo=tz.tzlocal())

    identifier = f'{experiment_name}_{metadata["mouseId"]}'
    session_id = f'{metadata["mouseId"]}_{metadata["sesId"]}'
    arena = f'Arena_{metadata["arena"]}'

    nwb = NWBFile(
        session_description=session_description,
        identifier=identifier,
        session_start_time=start_time,
        session_id=session_id,
        experiment_description=arena,
        experimenter=experimenter,
        lab=lab,
        institution=institution,

    )
    print('Created initial NWB')
    return nwb

def load_metadata_single_file(edf_filename, behavior_excel_file):
    """
    Extract subject and session metadata for one EDF file.

    Parameters:
    ### edf_filename [str]: Path to the EDF file.
    ### behavior_excel_file [str]: Path to the matching EthoVision Excel file.

    Returns:
    ### metadata [dict]: Combined metadata dictionary used to create the NWB file.
    """

    # Extract only the filename, without the full folder path.
    _, filename = os.path.split(edf_filename)
    filename_no_ext = filename.replace(".edf", "")

    # Define the expected EDF filename structure.
    pattern = (
        r"^TAINI_(?P<transmitter_id>\d{4})_"
        r"(?P<mouse_name>b\d+c\d+\.\d)_"
        r"(?P<subject_id>\d{4})_"
        r"(?P<date>\d{4}[-_]\d{2}[-_]\d{2})_"
        r"(?P<time>\d{2}-\d{2})-"
        r"(?P<timestamp>\d+)_"
        r"(?P<session_id>\w{2})_"
        r"(?P<increment>\d+)$"
    )

    # Match the EDF filename against the expected pattern.
    match = re.match(pattern, filename_no_ext)
    if match is None:
        raise ValueError(f"Filename not in expected format: {filename}")

    # Store all named groups from the filename pattern in a dictionary.
    metadata = match.groupdict()
    metadata["date"] = metadata["date"].replace("_", "-")

    # Read the first rows of the behavior Excel file, where metadata is stored.
    beh_header = pd.read_excel(behavior_excel_file, header=None, nrows=45)

    def get_value(label):
        """
        Find the value belonging to a metadata label in the behavior Excel header.
        """
        rows = beh_header[beh_header.iloc[:, 0].astype(str).str.lower() == label.lower()]
        if rows.empty:
            return None
        return rows.iloc[0, 1]

    # Extract subject metadata from the behavior Excel file.
    genotype = get_value("genotype")
    sex = get_value("sex")
    rfid = get_value("RFID")
    batch = get_value("batch")

    # Combine filename-derived metadata and behavior-file metadata into one dictionary.
    metadata.update({
        "edf_filename": filename,
        "mouseId": metadata["mouse_name"],
        "mouseName": metadata["mouse_name"],
        "sesId": metadata["session_id"],
        "transmitterId": metadata["transmitter_id"],
        "arena": batch,
        "species": "Mus musculus",
        "genotype": genotype,
        "sex": str(sex).lower() if sex is not None else None,
        "weight": None,
        "birthday": None,
        "rfid": rfid,
    })

    return metadata

def add_subject_info(nwb, info):
    """
    Adds the subject metadata to the NWB file.

    Parameters:
    ### nwb [pynwb.NWBFile]: NWB file object.
    ### info [dict]: Metadata dictionary containing subject information.

    Returns:
    ### nwb [pynwb.NWBFile]: NWB file object with subject information added.
    """

    # Convert date of birth to a timezone datetime object if available
    dob = info.get('birthday', None)
    date_of_birth = dob.to_pydatetime().replace(tzinfo=tz.tzlocal()) if dob is not None else None

    # Add subject metadata to the NWB file.
    nwb.subject = Subject(
        subject_id=info['mouseId'],
        description=info['mouseName'],
        species=info['species'],
        sex=info['sex'],
        genotype=info['genotype'],
        weight=str(info['weight']) if info.get('weight') is not None else None,
        date_of_birth=date_of_birth
    )
    return nwb


def add_electrode_info(nwb, transmitter_id):
    """
    Adds the electrode information to the NWB file.
    
    Parameters:
    ### nwb [pynwb.NWBFile]: NWB file object.
    ### transmitter_id [str]: Transmitter/device identifier.

    Returns:
    ### nwb [pynwb.NWBFile]: NWB file object with electrode metadata added.
    """
    electrode_info = filtering_version_1['electrode_info']

    # Add device and electrode information
    device = nwb.create_device(
        name=transmitter_id,
        description=transmitter_id,
        manufacturer='TaiNi'
    )

    nwb.add_electrode_column(name='label', description='label of electrode')

    for channel, details in electrode_info.items():
        location = details[0]
        AP, ML, DV = float(details[1]), float(details[2]), float(details[3])
        el_type = details[4]

        # create an electrode group for this channel
        electrode_group = nwb.create_electrode_group(
            name=channel,
            description=f'{channel}_{el_type}_{location}',
            device=device,
            location=location
        )
        # add this electrode's info to the NWB file
        nwb.add_electrode(
            x=AP, y=ML, z=DV, imp=np.nan,
            location=location,
            filtering='unknown',
            group=electrode_group,
            label=f'{el_type}_{location}'
        )
    print('Added electrode information')
    return nwb


def add_eeg_data(nwb, file):
    """
    Reads the EDF file, and adds the raw EEG data to the NWB file.

    Parameters:
    ### nwb [pynwb.NWBFile]: NWB file object.
    ### file [str]: Path to the EDF file.

    Returns:
    ### nwb [pynwb.NWBFile]: NWB file object with raw and filtered EEG added.
    ### raw_eeg [mne.io.Raw]: MNE Raw object used later to extract TTL annotations.
    """

    # load the electrode info from the settings file
    electrode_info = filtering_version_1['electrode_info']

    # read the edf file
    raw_eeg = mne.io.read_raw_edf(file)
    sfreq = raw_eeg.info['sfreq']

    # get the data using the keys of the electrode_info dictionary (see settings_general.py)
    data = raw_eeg.get_data(picks=list(electrode_info.keys()))

    # create electrode table
    all_table_region = nwb.create_electrode_table_region(
        region=list(range(len(electrode_info.keys()))),  # reference row indices 0 to N-1
        description='all electrodes'
    )

    # create electrical series holding the raw EEG data for the recorded channels
    raw_elec_series = ElectricalSeries(
        name='raw_EEG',
        data=H5DataIO(data=data.T, compression=True),  # transpose the data because (channels, data) format doesn't work
        electrodes=all_table_region,
        starting_time=0.,
        rate=sfreq  # sampling frequency
    )
    nwb.add_acquisition(raw_elec_series)

    # also add the filtered EEG data to the NWB object
    nwb = add_filtered_eeg(nwb, raw_eeg, sfreq, all_table_region)  # add filtered eeg data

    print('Added EEG data')
    return nwb, raw_eeg


def add_filtered_eeg(nwb, raw, s_freq, all_table_region):
    """
    Filters the raw EEG data and adds this to the NWB file.

    Parameters:
    ### nwb [pynwb.NWBFile]: NWB file object.
    ### raw [mne.io.Raw]: Raw EEG recording loaded from the EDF file.
    ### s_freq [float]: Original EEG sampling frequency.
    ### all_table_region [pynwb.core.DynamicTableRegion]: Electrode table region.

    Returns:
    ### nwb [pynwb.NWBFile]: NWB file object with filtered EEG added.
    """
    electrode_info = filtering_version_1['electrode_info']
    lcut, hcut = filtering_version_1['lcut'], filtering_version_1['hcut']
    low_val, high_val = filtering_version_1['low_val'], filtering_version_1['high_val']
    art = filtering_version_1['art']

    # if 3-chamber, and we want to resample to a specific frequency, do so
    if resample_freq is not None:
        raw.resample(resample_freq)
        print(f'Resampled EEG data from {s_freq} Hz to {resample_freq} Hz')
        s_freq = resample_freq  # set s_freq to the sampling frequency that data has been resampled to

    # filter the EEG data (all channels) and put into an array
    filtered_eeg = np.array([
        filter_eeg(raw[chan][0][0], filter_method, s_freq, lcut, hcut, low_val, high_val, art)
        for chan in electrode_info.keys()
    ])

    # Create new ElectricalSeries object to hold the filtered EEG, and add to nwb
    filt_elec_series = ElectricalSeries(
        name='filtered_EEG',
        data=H5DataIO(data=filtered_eeg.T, compression=True),
        electrodes=all_table_region,
        starting_time=0.,
        rate=float(s_freq),
        filtering=f'5th Order Bandpass butterwort Filter. Low:{lcut} Hz, High: {hcut}, low_val:{low_val}, high_val:{high_val}, art:{art}'
    )
    nwb.add_acquisition(filt_elec_series)

    return nwb


def add_ttl(nwb, raw):
    """
    Adds the TTL pulse information to the NWB file. The points of the TTL pulses are later
    used to align the EEG and the video-derived spatial or behavioural information.

    Parameters:
    ### nwb [pynwb.NWBFile]: NWB file object.
    ### raw [mne.io.Raw]: MNE Raw object containing EDF annotations.

    Returns:
    ### nwb [pynwb.NWBFile]: NWB file object with TTL_1 events added.
    """
    # we only need the SYNC_1 onsets, so get the time-stamps of these onsets
    ttl_data = raw.annotations.description
    ttl_data_sync_1 = np.delete(ttl_data, np.where(ttl_data == "SYNC_0"))
    ttl_timestamps = np.delete(raw.annotations.onset, np.where(ttl_data == "SYNC_0"))

    # TTL object needs data values, so parse these and keep only those of SYNC_1 onsets
    ttl_data_values = np.array([int(item.split('_')[1]) for item in ttl_data])
    ttl_data_values = np.delete(ttl_data_values, np.where(ttl_data == "SYNC_0"))

    # create a TTL events object
    ttl_events = TTLs(
        name='TTL_1',
        description='TTL 1 events from EEG annotations (SYNC_1 onsets)',
        timestamps=ttl_timestamps,
        data=ttl_data_values,
        labels=ttl_data_sync_1
    )

    nwb.add_acquisition(ttl_events)
    return nwb


def main():
    """
    Run the single-file EDF-to-NWB conversion workflow.

    The user selects one EDF file, its matching EthoVision behavior Excel file,
    and an output folder. The script extracts metadata, creates an NWB file,
    adds subject and electrode information, stores raw and filtered EEG data,
    adds TTL synchronization events, and saves the final NWB file.
    """

    # Ask for the experiment name
    experiment_name = input('Experiment name (e.g. 3c_sociability or resting_state): ')

    # Select the EDF file
    print("Select the EDF file")
    edf_file = select_file("Select the EDF file", filetypes=(("EDF files", "*.edf"), ("All files", "*.*")))

    # Select the behavior file
    print("Select the matching behavior Excel file")
    behavior_excel_file = select_file("Select the matching behavior Excel file")

    # Select output folder
    print("Select or create a folder to hold the output NWB file")
    nwb_output_folder = select_or_create_folder("Select or create a folder to hold the output NWB file")

    print(f"Creating NWB with EEG data from EDF file {os.path.basename(edf_file)}")

    # Extract metadata
    metadata = load_metadata_single_file(edf_file, behavior_excel_file)

    print("Loaded metadata:")
    for key, value in metadata.items():
        print(f"{key}: {value}")

    # Create NWB object
    nwb = create_nwb_file(metadata, experiment_name)

    nwb_filename = f'{experiment_name}_{metadata["mouseId"]}.nwb'
    save_nwb_to = os.path.join(nwb_output_folder, nwb_filename)

    if os.path.isfile(save_nwb_to):
        print(f"File {nwb_filename} already exists. Stopping.")
        return

    # Add subject metadata, electrode metadata, raw/filtered EEG data, and TTL event
    nwb = add_subject_info(nwb, metadata)
    nwb = add_electrode_info(nwb, str(metadata["transmitterId"]))
    nwb, raw = add_eeg_data(nwb, edf_file)
    nwb = add_ttl(nwb, raw)

    # Write the completed NWB file to disk
    with NWBHDF5IO(save_nwb_to, "w") as io:
        io.write(nwb)

    print(f"Saved NWB file to: {save_nwb_to}")

    raw.close()

if __name__ == "__main__":
    main()
    print('Done!')