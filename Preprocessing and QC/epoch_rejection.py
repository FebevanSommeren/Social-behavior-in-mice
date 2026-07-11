"""
Epoch rejection and cleaning utilities for MNE epoch files.

This script provides helper functions for cleaning frame-based EEG epoch files.
The workflow renames channels based on the subject's batch-specific electrode
configuration, sets montage information, detects and removes flat signal
segments, rejects epochs with unusually high or low peak-to-peak amplitude, and
saves cleaned epoch files.

The script can be used in two ways:
- run on one file for testing and visual inspection
- run on a folder of epoch files to batch-process all subjects

Main cleaning steps:
1. Rename channels and select EEG channels.
2. Detect epochs with flat signal windows.
3. Reject epochs with high peak-to-peak amplitude.
4. Reject epochs with low peak-to-peak amplitude.
5. Save cleaned epoch files and print rejection summaries.
"""
import os
import mne
import numpy as np
from pathlib import Path
import pandas as pd
import re
from mrondes_files.helper_functions import select_folder

from mrondes_files.settings_general import filtering_version_1, filtering_version_2
from mrondes_files.eeg_filter_functions import *

def get_filtering_version_from_subject(subject_id):
    """
    Select the filtering version that should be used for a subject.

    This function extracts the batch number from a subject ID and returns the
    corresponding filtering settings. Subjects from batches 1 and 2 use
    filtering_version_1, while subjects from batch 3 use filtering_version_2.

    Parameters:
    ### subject_id [str]: Subject ID containing the batch number.

    Returns:
    #### filtering_version [dict]: Filtering settings corresponding
        to the subject's batch.
    """
    
    match = re.search(r"b(\d+)c", subject_id)

    if match is None:
        raise ValueError(f"Could not determine batch from subject_id: {subject_id}")

    batch = int(match.group(1))
    print("batch:", batch)

    if batch in [1, 2]:
        return filtering_version_1

    if batch == 3:
        return filtering_version_2

    raise ValueError(f"Unknown batch {batch} for subject_id: {subject_id}")

def rename_channels_for_filtering(epochs, subject_id=None):
    """
    Rename epoch channels and set montage information for connectivity filtering.

    Parameters:
    ### epochs [mne.Epochs]: Epochs object containing EEG data and metadata.
    ### subject_id [str | None]: Subject ID used to determine which filtering
        version should be applied. If None, the subject ID is read from
        epochs.metadata["subject_id"].

    Returns:
    ### epochs [mne.Epochs]: Epochs object with renamed channels and montage set.
    ### picks [numpy.ndarray]: Indices of EEG channels included in the montage.
        EMG channels are excluded.
    """
    epochs = epochs.copy()

    # Try to get the subject ID from metadata if it was not provided manually
    if subject_id is None:
        if epochs.metadata is not None and "subject_id" in epochs.metadata.columns:
            subject_id = epochs.metadata["subject_id"].iloc[0]
        else:
            raise ValueError(
                "Please provide subject_id, e.g. rename_channels_for_filtering(epochs, 'b1c1.1')"
            )
    
    # Select the filtering settings based on the subject's batch
    filtering_version = get_filtering_version_from_subject(subject_id)
    electrode_info = filtering_version["electrode_info"]

    # Create a mapping from original channel names to standardized channel names
    rename_map = {
        old_name: values[0]
        for old_name, values in electrode_info.items()
        if old_name in epochs.ch_names
    }

    if rename_map:
        epochs.rename_channels(rename_map)
    else:
        print("No renaming needed; channels already seem renamed.")

    # Create channel-position dictionary for EEG channels onl
    ch_pos = {
        values[0]: values[1:4]
        for values in electrode_info.values()
        if values[4] != "emg" and values[0] in epochs.ch_names
    }

    # Create an MNE montage from the channel positions
    montage = mne.channels.make_dig_montage(
        ch_pos=ch_pos,
        coord_frame="head",
    )

    # Attach montage information to the epochs object
    epochs.set_montage(montage, on_missing="ignore")

    # Select only EEG channels included in the montage
    picks = mne.pick_channels(
        epochs.ch_names,
        include=list(ch_pos.keys())
    )

    return epochs, picks

def get_eeg_data(epochs):
    """
    Extract EEG data from an MNE Epochs object

    Parameters:
    ### epochs [mne.Epochs]: Epochs object containing EEG/EMG data.

    Returns:
    ### data [numpy.ndarray]: EEG data array with shape:
        (n_epochs, n_eeg_channels, n_times).
    """
    picks = mne.pick_types(
        epochs.info,
        eeg=True,
        emg=False
    )
    data = epochs.get_data()[:, picks, :]
    return data


def filter_flat_parts(epochs, picks): 
    """
    Detect and remove epochs containing flat signal segments

    This function checks each epoch for time windows in which the signal
    range is very small. For each window, the peak-to-peak amplitude is
    calculated for all selected channels. A window is marked as bad if enough
    channels are flat. An epoch is marked as bad if enough of its windows are bad.

    Parameters:
    ### epochs [mne.Epochs]: Epochs object containing the data to clean
    ### picks [numpy.ndarra]: Channel indices to include in the flat-signal check


    Returns:
    ### epochs_clean [mne.Epochs]: Copy of the epochs object with flat epochs removed
    ### flat_original_idx [list]: Original epoch indices corresponding to the
        dropped flat epochs.
    """
    # Extract only the selected channels.
    data = epochs.get_data()[:, picks, :]  # shape: n_epochs, n_channels, n_times (exclude emg channels)
    sfreq = epochs.info["sfreq"]

    # Flat-detection parameters: tuned by trial and error
    win_s = 0.02 # window length in sec 
    win = int(win_s * sfreq) # window length in samples
    flat_threshold = 1.1e-5  # peak-to-peak threshold for a flat channel
    min_bad_channels_frac = 0.1 # fraction of channels that must be flat
    min_bad_epoch_frac = 0.1 # fraction of windows that must be bad

    bad_epochs = []

    # Loop over epochs
    for ei in range(data.shape[0]):
        n_windows = 0
        n_bad_windows = 0

        # Slide a window across the epoch
        for start in range(0, data.shape[2] - win):
            stop = start + win
            n_windows += 1

            # Calculate peak-to-peak amplitude for each channel in this window
            ptp = np.ptp(data[ei, :, start:stop], axis=1)
            
            # Mark channels as flat if their signal range is below threshold
            flat_chs = ptp < flat_threshold

            # Mark this window as bad if enough channels are flat
            if flat_chs.mean() >= min_bad_channels_frac:
                n_bad_windows += 1

        # Calculate fraction of bad windows in this epoch
        bad_epoch_frac = n_bad_windows / n_windows

        # Mark epoch as bad if enough windows were flat
        if bad_epoch_frac >= min_bad_epoch_frac:
            bad_epochs.append(ei)

    print("Flat epochs positions:", bad_epochs)

    # Convert positions in the current epochs object back to original epoch indices
    flat_original_idx = epochs.selection[bad_epochs].tolist()

    # Drop them 
    epochs_clean = epochs.copy()
    epochs_clean.drop(
        bad_epochs,
        reason="FLAT",
    )

    print(f"Dropped {len(bad_epochs)} / {len(epochs)} flat epochs")
    print("Flat original indices:", flat_original_idx)

    # Return the epochs without the dropped ones 
    return epochs_clean, flat_original_idx


def plot_flat(epochs, idx):
    """
    Plot epochs that were rejected because of flat signal segments

    Parameters:
    ### epochs [mne.Epochs]: Original epochs object before rejected epochs were dropped.
    ### idx [list]: Positions of the flat epochs to inspect.

    Returns:
    #### None: The function displays an interactive MNE plot.
    """
    epochs[idx].plot(
            n_epochs=min(len(idx), 20),
            title="Flat rejected epochs",
            block=True,
        )


def reject_high_ptp(epochs, percentile=99):
    """
    Detect and remove epochs with unusually high peak-to-peak amplitude.

    The rejection threshold is adaptive. It uses the lower value of:
    - the (99th) percentile cutoff,
    - 1.2 times the average of the 10 highest epoch peak-to-peak values

    Parameters:
    ### epochs [mne.Epochs]: Epochs object containing EEG data.
    ### percentile [float]: Percentile used to define the high-amplitude cutoff.
        Default is 99.

    Returns:
    ### epochs_clean [mne.Epochs]: Copy of the epochs object with high-amplitude
        epochs removed.
    ### bad_original_idx [list]: Original epoch indices corresponding to the
        dropped high peak-to-peak epochs.
    """
    data = get_eeg_data(epochs)

    # max peak-to-peak over EEG channels per epoch
    epoch_ptp = np.ptp(data, axis=2).max(axis=1)

    # Warn if there are few epochs, because percentile-based thresholds
    # can become unstable with small sample sizes
    if len(epoch_ptp) < 20:
        print(f"Warning: very few epochs ({len(epoch_ptp)}), adaptive cutoff may be unstable")
    else:
        print(f"length epoch_ptp is {len(epoch_ptp)}")
    
    # Calculate percentile-based cutoff
    percentile_cutoff = np.percentile(epoch_ptp, percentile)

    # Calculate a cutoff based on the largest epoch amplitudes
    top10_cutoff = np.mean(np.sort(epoch_ptp)[-min(10, len(epoch_ptp)):]) 

    # Use the more conservative/lower cutoff
    ptp_cutoff = min(percentile_cutoff, top10_cutoff * 1.2)

    print(f"99th percentile cutoff: {percentile_cutoff * 1e6:.2f} µV")
    print(f"Top10 average cutoff: {top10_cutoff * 1e6:.2f} µV")
    print(f"Final high cutoff: {ptp_cutoff * 1e6:.2f} µV")

    # Find epochs above the high-amplitude threshold
    bad_pos = np.where(epoch_ptp >= ptp_cutoff)[0].tolist()
    
    # Convert positions in the current epochs object back to original indices
    bad_original_idx = epochs.selection[bad_pos].tolist()

    print(f"High PTP cutoff ({percentile}th percentile): {ptp_cutoff * 1e6:.2f} µV")
    print("High PTP epoch positions:", bad_pos)
    print("High PTP original indices:", bad_original_idx)

    # Drop high-amplitude epochs
    epochs_clean = epochs.copy()
    epochs_clean.drop(
        bad_pos,
        reason="HIGH_PTP"
    )

    return epochs_clean, bad_original_idx


def reject_low_ptp(epochs, percentile=1):
    """
    Detect and remove epochs with unusually low peak-to-peak amplitude.

    The rejection threshold is adaptive. It uses the higher value of:
    - the selected percentile cutoff, for example the 1st percentile
    - 0.8 times the average of the 10 lowest epoch peak-to-peak values

    Parameters:
    ### epochs [mne.Epochs]: Epochs object containing EEG data.
    ### percentile [float]: Percentile used to define the low-amplitude cutoff.
        Default is 1.

    Returns:
    #### epochs_clean [mne.Epochs]: Copy of the epochs object with low-amplitude
        epochs removed.
    #### bad_original_idx [list]: Original epoch indices corresponding to the
        dropped low peak-to-peak epochs.
    """
    data = get_eeg_data(epochs)

    # min peak-to-peak over EEG channels per epoch
    # low values indicate at least one very flat EEG channel
    epoch_ptp = np.ptp(data, axis=2).min(axis=1)

    # Warn if there are few epochs, because percentile-based thresholds
    # can become unstable with small sample sizes.
    if len(epoch_ptp) < 20:
        print(f"Warning: very few epochs ({len(epoch_ptp)}), adaptive cutoff may be unstable")
    else:
        print(f"length epoch_ptp is {len(epoch_ptp)}")
    # percentile cutoff
    percentile_cutoff = np.percentile(epoch_ptp, percentile)

    # average of 10 lowest
    bottom10_cutoff = np.mean(np.sort(epoch_ptp)[:min(10, len(epoch_ptp))])

    # Use the more conservative/higher low-amplitude cutoff
    ptp_cutoff = max(percentile_cutoff, bottom10_cutoff * 0.8)

    print(f"1st percentile cutoff: {percentile_cutoff * 1e6:.2f} µV")
    print(f"Bottom10 average cutoff: {bottom10_cutoff * 1e6:.2f} µV")
    print(f"Final low cutoff: {ptp_cutoff * 1e6:.2f} µV")

    # Find epochs below the low-amplitude threshold
    bad_pos = np.where(epoch_ptp <= ptp_cutoff)[0].tolist()

    # Convert positions in the current epochs object back to original indices
    bad_original_idx = epochs.selection[bad_pos].tolist()

    print(f"Low PTP cutoff ({percentile}th percentile): {ptp_cutoff * 1e6:.2f} µV")
    print("Low PTP epoch positions:", bad_pos)
    print("Low PTP original indices:", bad_original_idx)

    # Drop low-amplitude epochs
    epochs_clean = epochs.copy()
    epochs_clean.drop(
        bad_pos,
        reason="LOW_PTP"
    )

    return epochs_clean, bad_original_idx


def test_low(input_file="frame based epochs d2 run2/epochs_b2c1.2-epo.fif"):
    """
    Test low peak-to-peak rejection on one epoch file

    Parameters:
    ### input_path [str]: Path to the epoch file to test.

    Returns:
    ### None: It plots low ptp rejected epochs
    """
    epochs = mne.read_epochs(input_file)
    renamed_epochs, picks = rename_channels_for_filtering(epochs)
    picks = mne.pick_types(renamed_epochs.info, eeg=True, emg=False)
    
    # Apply low peak-to-peak rejection
    epochs_clean, low_idx = reject_low_ptp(renamed_epochs)
    
    # Plot rejected epochs for visual inspection
    epochs[low_idx].plot(
            n_epochs=min(len(low_idx), 20),
            title="Low ptp dropped epochs",
            block=True,
    )


def test_one_file(
    input_path,
    output_folder="necessary epoch files d2",
    output_suffix="-cleaned-epo"
    ):
    """
    Test the full epoch-cleaning workflow on one epoch file.

    Parameters:
    ### input_path [str]: Path to the input epoch file
    ### output_folder [str]: Folder where the cleaned epoch file is saved.
    ### output_suffix [str]: Suffix added to the cleaned output filename.

    Returns:
    #### epochs_clean [mne.Epochs]: Cleaned epochs object after all rejection steps
    #### all_bad_idx [list]: Original epoch indices rejected by any cleaning step
    """
    
    # Load epoch file
    epochs = mne.read_epochs(
        input_path,
        preload=True
    )

    # Rename channels and get EEG channel picks for filtering
    renamed_epochs, picks = rename_channels_for_filtering(epochs)

    print(f"File: {input_path}")
    print(f"Before cleaning: {len(renamed_epochs)} epochs")

    # Remove epochs containing flat signal segments
    epochs_clean, flat_idx = filter_flat_parts(
        renamed_epochs,
        picks
    )

    print(f"After flat filtering: {len(epochs_clean)} epochs")

    # If all epochs were removed during flat filtering, inspect and stop
    if len(epochs_clean) == 0:
        plot_flat(epochs, flat_idx)
        return epochs_clean, flat_idx
    
    # Remove epochs with extremely high peak-to-peak amplitude
    epochs_clean, high_idx = reject_high_ptp(
        epochs_clean,
        percentile=99
    )

    print(f"After high PTP filtering: {len(epochs_clean)} epochs")

    # Remove epochs with unusually low peak-to-peak amplitude
    epochs_clean, low_idx = reject_low_ptp(
        epochs_clean,
        percentile=1
    )

    print(f"After low PTP filtering: {len(epochs_clean)} epochs")

    # Combine rejected epoch indices from all cleaning steps
    all_bad_idx = sorted(
        set(flat_idx + high_idx + low_idx)
    )

    print("Flat rejected:", flat_idx)
    print("High PTP rejected:", high_idx)
    print("Low PTP rejected:", low_idx)
    print("All rejected epochs:", all_bad_idx)

    # Show MNE drop log
    epochs_clean.plot_drop_log()

    # Plot rejected epochs by rejection type for visual inspection
    if flat_idx:
        epochs[flat_idx].plot(
            n_epochs=min(len(flat_idx), 20),
            title="Flat rejected epochs",
            block=True,
        )

    if high_idx:
        epochs[high_idx].plot(
            n_epochs=min(len(high_idx), 20),
            title="High PTP rejected epochs",
            block=True,
        )

    if low_idx:
        epochs[low_idx].plot(
            n_epochs=min(len(low_idx), 20),
            title="Low PTP rejected epochs",
            block=True,
        )

    if all_bad_idx:
        epochs[all_bad_idx].plot(
            n_epochs=min(len(all_bad_idx), 20),
            title="All rejected epochs",
            block=True,
        )

    print(f"Total rejected epochs: {len(all_bad_idx)}")

    # Create output filename from input filename.
    input_name = os.path.basename(input_path)
    input_name = input_name.replace("-epo.fif", "")

    output_name = f"{input_name}{output_suffix}.fif"
    output_path = os.path.join(output_folder, output_name)

    # Make sure output folder exists.
    os.makedirs(output_folder, exist_ok=True)

    # save cleaned epochs
    epochs_clean.save(
        output_path,
        overwrite=True,
    )
    print(f"Saved cleaned epochs to: {output_path}")

    return epochs_clean, all_bad_idx

def find_high_and_low_ptp_all_files(input_folder, output_csv="ptp_summary.csv"):
    """
    Calculate peak-to-peak amplitude summaries for all epoch files in a folder.

    Parameters:
    ### input_folder [str | pathlib.Path]: Folder containing epoch FIF files.
    ### output_csv [str]: name of the CSV file where the summary table is saved.
        Default is "ptp_summary.csv".

    Returns:
    #### summary_df [pandas.DataFrame]: DataFrame containing peak-to-peak summary
        statistics for each epoch file.
    """
    input_folder = Path(input_folder)

    rows = []

    # Find all MNE epoch files in the folder
    epoch_files = sorted(input_folder.glob("*-epo.fif"))

    print(f"Found {len(epoch_files)} epoch files")

    # Loop through each epoch file
    for file_path in epoch_files:
        print(f"Processing {file_path.name}")

        try:
            # Load the epoch file
            epochs = mne.read_epochs(
                file_path,
                preload=True,
                verbose=False,
            )
            # Select EEG channels only
            picks = mne.pick_types(
                epochs.info,
                eeg=True,
                emg=False,
            )
            # Extract EEG data
            data = epochs.get_data()[:, picks, :]

            # PTP per epoch, per channel
            ptp_per_epoch_channel = np.ptp(data, axis=2)

            # highest PTP channel in each epoch
            epoch_highest_ptp = ptp_per_epoch_channel.max(axis=1)

            # lowest PTP channel in each epoch
            epoch_lowest_ptp = ptp_per_epoch_channel.min(axis=1)

            # Extract subject ID from the filename
            subject_id = file_path.name.replace("epochs_", "").replace("-epo.fif", "")

            # Save summary statistics for this subject
            rows.append({
                "subject_id": subject_id,
                "file": file_path.name,
                "n_epochs": len(epochs),

                # Most extreme low and high PTP values across epochs
                "lowest_epoch_ptp_uv": epoch_lowest_ptp.min() * 1e6,
                "highest_epoch_ptp_uv": epoch_highest_ptp.max() * 1e6,

                # Typical low/high PTP values across epochs
                "median_lowest_ptp_uv": np.median(epoch_lowest_ptp) * 1e6,
                "median_highest_ptp_uv": np.median(epoch_highest_ptp) * 1e6,

                # Percentiles used to inspect possible low/high rejection thresholds
                "p1_lowest_ptp_uv": np.percentile(epoch_lowest_ptp, 1) * 1e6,
                "p99_highest_ptp_uv": np.percentile(epoch_highest_ptp, 99) * 1e6,

                "p5_lowest_ptp_uv": np.percentile(epoch_lowest_ptp, 5) * 1e6,
                "p95_highest_ptp_uv": np.percentile(epoch_highest_ptp, 95) * 1e6,
            })

        except Exception as e:
            # If a file fails, save the error 
            print(f"Failed {file_path.name}: {e}")

            rows.append({
                "subject_id": None,
                "file": file_path.name,
                "error": str(e),
            })

    # Convert all file summaries into a dataframe
    summary_df = pd.DataFrame(rows)

    # Save summary table as CSV
    summary_df.to_csv(output_csv, index=False)

    print(f"Saved summary to: {output_csv}")

    return summary_df

def summary_ptps():
    """
    Summarize high and low peak-to-peak amplitude values across all epoch files.

    This function runs find_high_and_low_ptp_all_files() on the selected input
    folder and saves the resulting summary table as a CSV file. It then prints
    the full summary table, identifies the subjects/files with the highest and
    lowest peak-to-peak values, and calculates the average of the 10 most extreme
    high and low PTP values.

    Returns:
    ### None: this function prints summary information and saves the PTP summary CSV
    """
    # Calculate PTP summary statistics for all epoch files in the folder
    ptp_summary = find_high_and_low_ptp_all_files(
        input_folder="frame based epochs d2 run2",
        output_csv="ptp_summary_d2_run2.csv",
    )

    # Print the full summary dataframe
    print(ptp_summary)

    # Show the 10 files with the highest maximum PTP values
    ptp_summary.sort_values(
        "highest_epoch_ptp_uv",
        ascending=False
    ).head(10)

    # Show the 10 files with the lowest minimum PTP values
    ptp_summary.sort_values(
    "lowest_epoch_ptp_uv",
    ascending=True
    ).head(10)

    # Highest PTP animal
    highest_row = ptp_summary.loc[
        ptp_summary["highest_epoch_ptp_uv"].idxmax()
    ]

    print("\nHighest PTP:")
    print(highest_row)


    # Lowest PTP animal
    lowest_row = ptp_summary.loc[
        ptp_summary["lowest_epoch_ptp_uv"].idxmin()
    ]

    print("\nLowest PTP:")
    print(lowest_row)

    print(
        "Highest PTP animal:",
        highest_row["subject_id"],
        f'({highest_row["highest_epoch_ptp_uv"]:.2f} µV)'
    )

    print(
        "Lowest PTP animal:",
        lowest_row["subject_id"],
        f'({lowest_row["lowest_epoch_ptp_uv"]:.2f} µV)'
    )

    # Average of the 10 highest maximum PTP values
    top10_high = ptp_summary.nlargest(
        10,
        "highest_epoch_ptp_uv"
    )

    avg_top10_high = top10_high["highest_epoch_ptp_uv"].mean()

    print(
        f"Average of 10 highest PTP values: "
        f"{avg_top10_high:.2f} µV"
    )

    # Average of the 10 lowest minimum PTP values
    top10_low = ptp_summary.nsmallest(
        10,
        "lowest_epoch_ptp_uv"
    )

    avg_top10_low = top10_low["lowest_epoch_ptp_uv"].mean()

    print(
        f"Average of 10 lowest PTP values: "
        f"{avg_top10_low:.2f} µV"
    )

    print(top10_high[
        ["subject_id", "highest_epoch_ptp_uv"]
    ])

    print(top10_low[
        ["subject_id", "lowest_epoch_ptp_uv"]
    ])

def check_bad_epoch_percentage(raw_epoch_folder, cleaned_epoch_folder):
    """
    Check the percentage of rejected epochs for each cleaned epoch file.

    This function compares the number of epochs in the original epoch files
    with the number of epochs remaining in the cleaned epoch files. For each
    subject, it calculates how many epochs were removed during cleaning and
    prints the percentage of rejected epochs.

    Parameters:
    ### raw_epoch_folder [str | pathlib.Path]: Folder containing the original
        epoch FIF files.
    ### cleaned_epoch_folder [str | pathlib.Path]: Folder containing the cleaned
        epoch FIF files.

    Returns:
    ### None: The function prints the number and percentage of rejected epochs per subject.
    """
    raw_epoch_folder = Path(raw_epoch_folder)
    cleaned_epoch_folder = Path(cleaned_epoch_folder)

    # Loop through all raw epoch files
    for raw_file in sorted(raw_epoch_folder.glob("*-epo.fif")):
        # Extract subject ID 
        subject_id = raw_file.name.replace("epochs_", "").replace("-epo.fif", "")

        # Build the expected cleaned filename
        cleaned_file = cleaned_epoch_folder / raw_file.name.replace(
            "-epo.fif",
            "_cleaned-epo.fif"
        )

        # Skip this subject if the cleaned file is missing
        if not cleaned_file.exists():
            print(f"{subject_id}: cleaned file missing")
            continue
        
        # Load raw and cleaned epochs
        raw_epochs = mne.read_epochs(raw_file, preload=False, verbose=False)
        cleaned_epochs = mne.read_epochs(cleaned_file, preload=False, verbose=False)

        # Count epochs before and after cleaning
        n_before = len(raw_epochs)
        n_after = len(cleaned_epochs)
        
        # Calculate number and percentage of rejected epochs
        n_bad = n_before - n_after
        bad_percent = n_bad / n_before * 100

        # Print summary for this subject
        print(
            f"{subject_id}: "
            f"{n_bad}/{n_before} bad epochs "
            f"({bad_percent:.1f}%), "
            f"{n_after} remaining"
        )

        # Warn if almost all epochs were rejected
        if bad_percent >= 99:
            print("  ⚠️ 99% or more bad epochs")

def filter_epochs(epochs):
    """
    Apply the full epoch-cleaning workflow to one MNE Epochs object

    This function renames channels according to the subject's filtering version,
    applies flat-signal rejection, high peak-to-peak rejection, and low
    peak-to-peak rejection. It prints the number of epochs remaining after each
    cleaning step and returns the cleaned epochs together with all rejected
    original epoch indices.
    
    Parameters:
    ### epochs [mne.Epochs]: Epochs object to clean.

    Returns:
    ### epochs_clean [mne.Epochs]: Cleaned epochs object after all filtering steps.
    ### all_bad_idx [list]: Original epoch indices rejected by any filtering step.
    """
    # Rename channels, set montage information, and get EEG channel picks
    renamed_epochs, picks = rename_channels_for_filtering(epochs)

    print(f"Before cleaning: {len(renamed_epochs)} epochs")

    # Filter flat parts
    epochs_clean, flat_idx = filter_flat_parts(
        renamed_epochs,
        picks
    )
    print(f"After flat filtering: {len(epochs_clean)} epochs")

    # If all epochs were removed, plot the rejected flat epochs and stop
    if len(epochs_clean) == 0:
        plot_flat(epochs, flat_idx)
        return epochs_clean, flat_idx
    
    # Filter very high peak-to-peak amplitude
    epochs_clean, high_idx = reject_high_ptp(
        epochs_clean,
        percentile=99
    )
    print(f"After high PTP filtering: {len(epochs_clean)} epochs")

    # Filter very low peak-to-peak amplitude
    epochs_clean, low_idx = reject_low_ptp(
        epochs_clean,
        percentile=1
    )
    print(f"After low PTP filtering: {len(epochs_clean)} epochs")

    # Combine rejected epoch indices across all filtering steps
    all_bad_idx = sorted(
        set(flat_idx + high_idx + low_idx)
    )

    print("Flat rejected:", flat_idx)
    print("High PTP rejected:", high_idx)
    print("Low PTP rejected:", low_idx)
    print("All rejected epochs:", all_bad_idx)

    return epochs_clean, all_bad_idx

def process_folder(input_folder, output_folder, overwrite=False):
    """
    Apply the full epoch-cleaning pipeline to all epoch files in a folder
    For each file, it loads the epochs, applies the filtering
    pipeline using filter_epochs(), and saves the cleaned epochs to the output
    folder.

    Parameters:
    ### input_folder [str | pathlib.Path]: Folder containing the original epoch
        FIF files.
    ### output_folder [str | pathlib.Path]: Folder where cleaned epoch files
        should be saved.
    ### overwrite [bool]: Whether to overwrite existing cleaned files.
        Default is False.

    Returns:
    ### None: The function saves cleaned epoch files and prints progress information.
    """
    input_folder = Path(input_folder)
    output_folder = Path(output_folder)

    # create output folder if needed
    output_folder.mkdir(parents=True, exist_ok=True)

    # find all epoch fif files
    epoch_files = sorted(input_folder.glob("*-epo.fif"))

    print(f"Found {len(epoch_files)} epoch files")

    # Loop through each epoch file
    for file_path in epoch_files:
        print("\n" + "=" * 60)
        print(f"Processing: {file_path.name}")

        try:
            # load epochs
            epochs = mne.read_epochs(
                file_path,
                preload=True,
                verbose=True,
            )

            # run filtering pipeline
            cleaned_epochs, all_bad_idx = filter_epochs(
                epochs
            )
            print(f"Total rejected epochs: {len(all_bad_idx)}")

            # create output filename
            output_name = file_path.stem.replace(
                "-epo",
                "_cleaned-epo",
            )
            output_path = output_folder / f"{output_name}.fif"

            # save cleaned epochs
            cleaned_epochs.save(
                output_path,
                overwrite=overwrite,
            )
            print(f"Saved cleaned file to:")
            print(output_path)

        except Exception as e:
            print(f"ERROR processing {file_path.name}")
            print(e)

    print("\nFinished processing all files.")

def main():
    """
    Run the full epoch-cleaning workflow.
    This function lets you select an input folder, output folder, 
    It then processes all epoch files in the selected input folder using
    process_folder().

    Returns:
    ### None: The function saves cleaned epoch files to the selected output folder.
    """
    # Select input folder
    input_folder = select_folder("select input folder (epoch files)")
    
    # Select output folder
    output_folder = select_folder("select or create folder to save filtered epoch files")
    
    # Process input folder
    process_folder(input_folder, output_folder, overwrite=True)

    # epochs_clean, bad_idx = test_one_file("frame based epochs d2 r3/epochs_b2c3.2-epo.fif")
    # test_low("frame based epochs d2 run2/epochs_b2c1.2-epo.fif")
    # check_bad_epoch_percentage(raw_epoch_folder="necessary epoch files d3", cleaned_epoch_folder="necessary epoch files d3/filtered epochs")
    # test_one_file()


if __name__ == "__main__":
    main()