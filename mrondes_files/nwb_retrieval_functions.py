"""
File that holds functions that can be used to retrieve data from a NWB file given its filename
MIRTHE RONDE
"""
import re
import numpy as np
from pynwb import NWBHDF5IO


def get_eeg(nwb_file_path, eeg_type, segment=(0, -1), channel_names=True):
    """
    Handy function that retrieves either the raw or filtered EEG data from a NWB file.

    Parameters:
    ### nwb_file_path [str]: Path to the NWB file
    ### eeg_type [str]: Name of the EEG acquisition to retrieve. Either
        "filtered_EEG" or "raw_EEG".
    ### segment [tuple]: Start and stop sample indices for the segment to extract.
        Default is (0, -1), which returns almost the full recording.
    ### channel_names [bool]: Whether to also return channel location information.
        Default is True.

    Returns:
    ### eeg [numpy.ndarray]: EEG data array with shape (n_channels, n_samples).
    ### channel_locations [numpy.ndarray]: Channel location labels from the NWB
        electrode table. Returned only when channel_names is True.
    :return:
    """
    with NWBHDF5IO(nwb_file_path, "r") as io:
        nwb = io.read()

        eeg = nwb.acquisition[eeg_type].data[segment[0]: segment[1]].T
        if not channel_names:
            return eeg

        return eeg, nwb.electrodes.location.data[:]  # return eeg segment and also channel info


def get_package_loss(nwb_filepath, segment):
    """
    Retrieves the raw EEG from the NWB file, searches and returns package loss information
    in two forms:
        - ploss_signal : raw signal containing np.nan values (without interpolating)
        - ploss_samples : sample indexes where there is package loss (more useful)
    
    Parameters:
    ### nwb_filepath [str]: Path to the NWB file.
    ### segment [tuple]: Start and stop sample indices of the EEG segment to inspect.

    Returns:
    ### ploss_signal [dict]: Dictionary mapping channel locations to EEG arrays
        where rejected/package-loss samples are represented as NaN.
    ### ploss_samples [dict]: Dictionary mapping channel locations to sample
        indices where rejected/package-loss samples occurred.
    """
    with NWBHDF5IO(nwb_filepath, "r") as io:
        nwb = io.read()
        filtering = nwb.acquisition['filtered_EEG'].filtering
        locations = nwb.electrodes.location.data[:]

        # Parse filtering info
        f_info = re.search('low_val:(.+),.+high_val:(.+),.+art:(.+)', filtering)
        low_val, high_val, art = float(f_info[1]), float(f_info[2]), f_info[3]
        art = None if art == 'None' else float(art) # FIX

        # take the data from the raw eeg that corresponds to this epoch
        raw_eeg_seg = nwb.acquisition['raw_EEG'].data[segment[0]: segment[1]].T

        ploss_signal, ploss_samples = {}, {}  # to store data in
        for signal, location in zip(raw_eeg_seg, locations):
            rej = np.where(signal > low_val, signal, np.nan)
            rej = np.where(signal < high_val, rej, np.nan)
            if art is not None: # NOTE: CHANGED from if art != 'None
                # art = float(f_info[3]) # NOTE: REMOVE line later 
                
                rej = np.where((rej > np.nanmean(rej) + art*np.nanstd(rej)) | (rej < np.nanmean(rej) - art*np.nanstd(rej)), np.nan, rej) # NOTE: changed np.mean --> np.nanmean
            ploss_signal[location] = rej
            ploss_samples[location] = np.where(np.isnan(rej))[0]

    return ploss_signal, ploss_samples