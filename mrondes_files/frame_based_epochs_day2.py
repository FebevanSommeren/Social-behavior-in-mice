"""
Create frame-based Day 2 sociability EEG epochs from NWB and EthoVision data.

This script aligns behavioral events from EthoVision output with EEG data stored
in NWB files. It detects periods in which the animal investigates the cup with
the mouse or the empty cup, converts these frame-based events into EEG sample
indices using adjusted video FPS and TTL/LED synchronization, and saves fixed-
length MNE epoch files per subject.

Original code by Mirthe Ronde; adapted for Day 2 sociability analysis.
Run with: python -m mrondes_files.frame_based_epochs_day2

This code is mostly written by M. Ronde's Team. I made some adjustments, but most of the logic
is the same. 
"""

# Libraries 
import re
import mne
import pickle
import ndx_events
import numpy as np
import pandas as pd
from pynwb import NWBHDF5IO

# All from mrondes_files (scripts written by M. Ronde's Team)
from settings_general import *
from helper_functions import *
from nwb_retrieval_functions import get_eeg, get_package_loss
from eeg_video_alignment_functions import adjust_fps, get_first_ttl_offset

def preprocess_behavior_excel(filepath):
    """
    Load an EthoVision Day 2 Excel file and extract cup-investigation columns.

    The function identifies whether the social stimulus mouse was placed on the
    left or right side and returns a simplified dataframe containing video frame
    numbers, time spent in the cup with the mouse, and time spent in the empty
    cup.

    Parameters:
    ### filepath [str]: Path to the EthoVision Excel file for one subject.

    Returns:
    ### clean_df [pandas.DataFrame]: Dataframe with columns 'frame', 'with mouse cup', and
        'without mouse cup'.
    """
    # Read Ethovision behavior excel file
    df = pd.read_excel(filepath, header=42)
    df = df.iloc[2:].reset_index(drop=True)

    # social stimulus (with mouse cup) location in excel file
    mouse_side = pd.read_excel(filepath, header=None).iloc[38, 1] # for day 2 38,1, for day 3 39,1 

    # Find the columns that contain the left and right cup-zone data.
    left_cup_col = [col for col in df.columns if re.search(r'left cup', col, re.IGNORECASE)][0]
    right_cup_col = [col for col in df.columns if re.search(r'right cup', col, re.IGNORECASE)][0]
    frame_col = df.columns[0] # The first column contains trial time

     # Use the recorded mouse side to decide which cup is the social stimulus
    if mouse_side == 'R':
        with_mouse_col = right_cup_col
        without_mouse_col = left_cup_col
    elif mouse_side == 'L':
        with_mouse_col = left_cup_col
        without_mouse_col = right_cup_col
    else:
        raise ValueError(f"Unexpected value in row 39, column B: {mouse_side}")

    # Create a simplified dataframe with only the columns needed for event extraction.
    clean_df = pd.DataFrame({
        'frame': df[frame_col],
        'with mouse cup': df[with_mouse_col],
        'without mouse cup': df[without_mouse_col]
    })

    return clean_df

def convert_binary_to_event_rows(df_bin):
    """
    Convert binary cup-investigation columns into START and STOP event rows.

    Parameters:
    ### df_bin [pandas.DataFrame]: Dataframe containing a frame column and binary behavior columns.

    Returns:
    ### pandas.DataFrame: Event dataframe with frame index, time, behavior name, and event type.
    """
    events = []

    # Loop over both behavior columns:
    for behavior in ['with mouse cup', 'without mouse cup']:
        # Clean the behavior column so it only contains 0 and 1 values.
        active = (
            df_bin[behavior]
            .replace("-", 0)  # '-' and missing values are treated as 0, meaning the behavior is not active.
            .fillna(0)
            .infer_objects(copy=False)
            .astype(int)
            .values
        )
        # Store the corresponding frame/time values.
        times = df_bin['frame'].values

        # Find behavior starts: START occurs when the signal changes from 0 to 1.
        start_idxs = np.where((active[:-1] == 0) & (active[1:] == 1))[0] + 1
        
        # Find behavior stops: STOP occurs when the signal changes from 1 to 0.
        stop_idxs = np.where((active[:-1] == 1) & (active[1:] == 0))[0] + 1

        # If the behavior is already active in the first frame, mark the first frame as a START.
        if active[0] == 1:
            start_idxs = np.insert(start_idxs, 0, 0)
        
        # If the behavior is still active in the last frame, mark the last frame as a STOP.
        if active[-1] == 1:
            stop_idxs = np.append(stop_idxs, len(active) - 1)

        # Handle mismatched START/STOP counts
        min_len = min(len(start_idxs), len(stop_idxs))
        if len(start_idxs) != len(stop_idxs):
            print(f"⚠️ Warning: mismatch in START/STOP for {behavior}. "
                  f"Using {min_len} matched pairs.")
            start_idxs = start_idxs[:min_len]
            stop_idxs = stop_idxs[:min_len]

        # Add one row for each START event.
        for idx in start_idxs:
            events.append({
                'Image index': idx,
                'Time': times[idx],
                'Behavior': behavior,
                'Behavior type': 'START'
            })
        
        # Add one row for each STOP event.
        for idx in stop_idxs:
            events.append({
                'Image index': idx,
                'Time': times[idx],
                'Behavior': behavior,
                'Behavior type': 'STOP'
            })

    # Convert all events to a dataframe and sort them in chronological order.
    return pd.DataFrame(events).sort_values('Time').reset_index(drop=True)

def merge_event_rows(beh_data):
    """
    (own version) Merge alternating START and STOP rows into one row per behavioral event.

    Parameters:
    ### beh_data [pandas.DataFrame]: Event dataframe containing paired START and STOP rows.

    Returns:
    ### pandas.DataFrame: Dataframe with one row per event, including start frame, stop frame,
        and event duration.
    
    
    """
    # Separate alternating rows into START and STOP rows
    start = beh_data.iloc[::2].reset_index(drop=True)
    stop = beh_data.iloc[1::2].reset_index(drop=True)

    # Safety check: Check whether each START row has a matching STOP row.
    if len(start) != len(stop):
        print(f"Warning: Mismatch after slicing: {len(start)} START vs {len(stop)} STOP")
        min_len = min(len(start), len(stop))
        start = start.iloc[:min_len]
        stop = stop.iloc[:min_len]
    
    merged_df = start.copy()

    # Add the start frame, stop frame, and event duration for each event.
    merged_df['Frame start'] = start['Image index']
    merged_df['Frame stop'] = stop['Image index']
    merged_df['Event duration'] = stop['Time'] - start['Time']

    # drop the columns we do not need
    cols_to_drop = [
        "Image index",
        "Time",
        "Observation type",
        "Source",
        "Time offset (s)",
        "Subject",
        "Comment",
        "Image file path",
        "Description",
        "Behavioral category",
        "Behavior type",
    ]

    existing_cols_to_drop = [col for col in cols_to_drop if col in merged_df.columns]
    return merged_df.drop(columns=existing_cols_to_drop)

def get_led_onsets(video_analysis_dir, batch_cage_name):
    """
    Loads the correct LED onset data from the pickle file which holds the LED
    onset data for all experiment videos, and returns LED onset frame indices

    Parameters:
    ### video video_analysis_dir [str]: Folder containing the led_states.pickle file.
    ### batch_cage_name [str]: Batch-cage identifier used to match the correct video.
    

    Returns:
    ### led_onsets [numpy.ndarray]: Frame indices where the LED changes from OFF to ON.
    """
    # Open the pickle file containing LED state arrays for all videos.
    with open(os.path.join(video_analysis_dir, 'led_states.pickle'), "rb") as f:
        led_states = pickle.load(f)

        # Split the batch-cage name into batch and cage parts.
        batch, cage = batch_cage_name.split('_')
        
        # Find video filenames that contain the cage identifier.
        movie_filename = [
            fn for fn in led_states.keys()
            if cage in fn
        ]

        # If no matching video is found, return an empty array so the subject can be skipped later.
        print(movie_filename) 
        if len(movie_filename) == 0:
            print(f"Warning: No matching video found for {batch_cage_name}")
            return np.array([])
    
        # if there's a repeat file for this subject, use that instead of the original file
        if len(movie_filename) != 1:
            movie_filename = [fn for fn in movie_filename if 'repeat' in fn] 

        # Load the LED state vector for the selected video.
        led_states = led_states[movie_filename[0]]

        # Detect LED onsets.
        # Onset = transition from 0 to 1, meaning OFF to ON.
        led_onsets = np.where((led_states[:-1] == 0) & (led_states[1:] == 1))[0] + 1
        return led_onsets


def frame_to_sample(video_frame, adjusted_fps, offset, s_freq):
    """
    Function that calculates the EEG sample from the video frame using the adjusted FPS and the calculated offset.
    It converts a video frame number to an EEG sample index.

    Parameters:
    ### video_frame [int | float]: Video frame to convert.
    adjusted_fps [float]: Adjusted video frame rate calculated from EEG TTL and LED onsets.
    offset [float]: Time offset between video time and EEG time, in seconds.
    s_freq [float]: EEG sampling frequency in Hz.

    Returns:
    ### [float]: EEG sample index corresponding to the video frame.
    """
    # go from video frame to seconds
    video_tp_secs = video_frame / adjusted_fps

    # first TTL onset always later in EEG than video, so to go from video tp in seconds to the eeg tp in seconds
    # we add the calculated offset
    eeg_tp_secs = video_tp_secs + offset

    return eeg_tp_secs * s_freq  # go to samples

def get_epoch_overlap(event):
    """
    Calculates the overlap each fixed epoch of 'desired_epoch_length' needs to have with the previous one in order
    to capture all data that falls within an event.

    Example:
    If the desired epoch length is 1 sec and an event lasts 2.4 seconds,
    cutting the event into non-overlapping 1-second epochs would give:
    epoch 1: 0.0 - 1.0 s
    epoch 2: 1.0 - 2.0 s
    This would leave the final 0.4 seconds uncovered.

    To cover the full 2.4-second event with three 1-second epochs, the epochs
    need to overlap slightly:
    epoch 1: 0.0 - 1.0 s
    epoch 2: 0.7 - 1.7 s
    epoch 3: 1.4 - 2.4 s
    Each epoch overlaps the previous one by 0.3 seconds.

    Parameters: 
    ### event [pandas.Series]: the interaction/event with start/stop time in frames and event duration
    
    Returns:
    ### overlap [float]: Epoch overlap in seconds
    """

    total_duration = event['Event duration']

    # let's calculate the number of epochs of length 'desired_epoch_length' that fit into the event
    # this is also the number of overlaps between all epochs if you would cut it at increments of
    # 'desired_epoch_length'
    num_full_epochs = int(total_duration // desired_epoch_length)

    # get the amount of seconds that would've made the last epoch equal to 'desired_epoch_length'
    missing_seconds = 1 - (total_duration - num_full_epochs)

    # now, if we divide the 'missing_seconds' by the 'num_full_epochs' (i.e. amount of epoch overlaps), we get the
    # needed amount of seconds each epoch has to overlap with the previous one to capture all data
    overlap = missing_seconds / num_full_epochs

    return overlap

def get_eeg_start_end_tps(adjusted_video_fps, event, offset, s_freq):
    """
    Convert behavioral event start and stop frames to EEG sample indices.

    If an event is shorter than the desired epoch length, the event window is
    padded equally on both sides before conversion to EEG samples.

    Parameters:
    ### adjusted_video_fps [float]: Adjusted video frame rate.
    ### event [pandas.Series]: Behavioral event row with frame start, frame stop, and duration.
    ### offset [float]: Time offset between video time and EEG time, in seconds.
    ### s_freq [float]: EEG sampling frequency in Hz.

    Returns:
    ### event_start, event_end [tuple[int, int]]: Start and end sample indices in the EEG recording.
    """
    # get the start and stop frame time-point of this event
    start_frame, stop_frame = int(event['Frame start']), int(event['Frame stop'])

    # total event duration
    event_duration = event['Event duration']

    # when the min_event_duration is None, we very likely get events that are shorter than the desired_epoch_length
    # however, it is also possible that the event_duration is shorter than the desired epoch length if we DO set the
    # min_event_duration
    # therefore we need to add EEG data on each side of the actual event to get to the desired epoch length.
    if event_duration < desired_epoch_length:
        missing_duration = desired_epoch_length - event_duration  # seconds
        missing_duration_frames = missing_duration * adjusted_video_fps  # in frames

        # get the amount of frames we need to add to each side of the event in order to make it of length
        # 'desired_epoch_length'
        to_subtract_and_add = missing_duration_frames / 2

        start_frame, stop_frame = np.floor(start_frame - to_subtract_and_add), np.ceil(stop_frame + to_subtract_and_add)

    # using the adjusted FPS and the offset of the first TTL, get the start/stop time-points of the event in samples
    event_start = int(frame_to_sample(start_frame, adjusted_video_fps, offset, s_freq))
    event_end = int(frame_to_sample(stop_frame, adjusted_video_fps, offset, s_freq))

    return event_start, event_end


def get_epochs(nwb_file_path, beh_data_subset, adjusted_video_fps, offset, s_freq, subject_id, genotype):
    """
    Create fixed-length MNE epochs for all usable behavioral events.
    Returns None if no usable epochs are created.

    Parameters:
    ### nwb_file_path [str]: Path to the subject's NWB file.
    ### beh_data_subset [pandas.DataFrame]: Cleaned behavioral event dataframe for one subject.
    ### adjusted_video_fps [float]: Adjusted video frame rate.
    ### offset [float]: Time offset between video and EEG time, in seconds.
    ### s_freq [float]: EEG sampling frequency in Hz.
    ### subject_id [str]: Subject identifier.
    genotype [str]: Subject genotype.

    Returns:
    ### all_epochs [mne.Epochs | None]: Concatenated epochs for the subject, or None if no usable epochs were
        created.
    """
    # Store the MNE Epochs objects created for each behavioral event
    all_event_epochs = []

    # Keep track of how many behavioral events are skipped during filtering
    skipped_events = 0

    # Optionally override package loss skipping for testing:
    # resampled = True  # ← uncomment to bypass package loss checks

    # Loop through each behavioral event for this subject
    for index, event in beh_data_subset.iterrows():
        # Convert the event start and stop frames from video time to EEG sample indices.
        event_start, event_end = get_eeg_start_end_tps(adjusted_video_fps, event, offset, s_freq)

        print(f"Event {index}: {event['Behavior']} from sample {event_start} to {event_end} "
              f"(duration: {(event_end - event_start) / s_freq:.2f} sec)")

        # Skip events that start before the EEG recording begins.
        # This can happen if the video event starts before the aligned EEG time point.
        if event_start < 0:
            print(f"⚠️ Skipping event {index} — starts before EEG recording: {event_start}")
            skipped_events += 1
            continue
        
        # Skip events that end before the start of the EEG recording.
        if event_end <= 0:
            print(f"⚠️ Skipping event {index} — ends before EEG recording: {event_end}")
            skipped_events += 1
            continue
        
        # Skip events that are still too short to create one full fixed-length epoch.
        # The minimum required length is desired_epoch_length converted to EEG samples.
        if event_end - event_start < desired_epoch_length * s_freq:
            print(f"⚠️ Skipping event {index} — too short after padding")
            skipped_events += 1
            continue
        
        # Extract the filtered EEG segment corresponding to this behavioral event
        event_eeg, chans = get_eeg(nwb_file_path, 'filtered_EEG', (event_start, event_end), True)
        
        # Skip the event if no EEG data could be extracted
        if event_eeg is None or event_eeg.size == 0 or event_eeg.shape[-1] == 0:
            print(f"⚠️ Skipping event {index} — empty EEG segment")
            skipped_events += 1
            continue
        
        # Check for package loss if data is not resampled
        if not resampled:
            event_duration = event_end - event_start  # in EEG samples
            too_much_package_loss = False

            # Load package-loss information for the EEG segment.
            ploss, _ = get_package_loss(nwb_file_path, (event_start, event_end))
            
            # Only check EEG channels
            chans_to_check = [chan for chan in chans if 'EMG' not in chan]

            for chan in chans_to_check:
                # Count missing samples for this channel
                package_loss = np.sum(np.isnan(ploss[chan]))  # for this channel in EEG samples
                
                # Skip the event if the fraction of missing samples is too high
                if (package_loss / event_duration) > package_loss_cutoff:
                    too_much_package_loss = True
                    break

            if too_much_package_loss:
                skipped_events += 1
                continue
        
        # Default to no overlap between fixed-length epochs.
        overlap = 0.0

        # If enabled, calculate how much overlap is needed to cover the full event.
        if overlap_epochs:
            overlap = get_epoch_overlap(event)

            # If required overlap is too large, set it back to zero 
            max_allowed_overlap = epoch_overlap_cutoff * desired_epoch_length
            if overlap > max_allowed_overlap:
                overlap = 0.0

        # Define channel types for MNE
        ch_types = ["emg" if "EMG" in chan else "eeg" for chan in chans]
        
        # Create an MNE info object describing channel names, sampling frequency, and channel types
        info = mne.create_info(ch_names=list(chans), sfreq=s_freq, ch_types=ch_types, verbose="WARNING")
        
        # Convert the EEG segment into an MNE RawArray
        raw = mne.io.RawArray(event_eeg, info, verbose="WARNING")

        # Split the EEG segment into fixed-length epochs
        epochs = mne.make_fixed_length_epochs(
            raw, duration=desired_epoch_length, overlap=overlap, preload=True, verbose="WARNING"
        )

        # Create metadata 
        metadata = pd.DataFrame({
            'subject_id': [subject_id] * len(epochs),
            'genotype': [genotype] * len(epochs),
            'event_n': [index + 1] * len(epochs),
            'event_part_n': range(1, len(epochs) + 1),
            'event_kind': [event["Behavior"]] * len(epochs),
            'total_event_duration': [event["Event duration"]] * len(epochs),
            'epoch_length': [desired_epoch_length] * len(epochs),
        })
        epochs.metadata = metadata
        
        # Store the epochs for this event so they can be combined later
        all_event_epochs.append(epochs)

    # If no events produced usable epochs, return None so the subject can be skipped
    if len(all_event_epochs) == 0:
        print(f'⚠️ No usable epochs were created for subject {subject_id}. Skipping.')
        return None

    # Combine all event-level Epochs objects into one Epochs object for this subject
    all_epochs = mne.concatenate_epochs(all_event_epochs, verbose="WARNING")

    print(f'\nSkipped {skipped_events} events ({skipped_events / len(beh_data_subset) * 100:.2f}%) due to filtering.')
    return all_epochs

def create_cleaned_event_df(beh_data, batch_cage, subject_id, genotype):
    """
    Clean START/STOP event rows and create one event dataframe per subject:
    Checks if there are an equal amount of START and STOP events per event type. If not, it will try to fix it,
    if it seems unfixable, it will skip the event in question.

    Parameters:
    ### beh_data [pandas.DataFrame]: Event dataframe containing START and STOP rows.
    ### batch_cage [str]: Batch-cage identifier for the subject.
    ### subject_id [str]: Subject identifier.
    ### genotype [str]: Subject genotype.

    Returns:
    ### beh_df [pandas.DataFrame]: Cleaned event dataframe with subject metadata and event durations.
    """
    # Create an empty dataframe to store the cleaned events
    beh_df = pd.DataFrame()

    # Process each behavior type separately
    for event_type in beh_data['Behavior'].unique():
        # Select only the rows belonging to the current behavior type
        beh_dat_event = beh_data[beh_data['Behavior'] == event_type]
        
        # Separate START and STOP rows to check whether they are paired correctly
        starts = beh_dat_event[beh_dat_event['Behavior type'] == 'START']
        stops = beh_dat_event[beh_dat_event['Behavior type'] == 'STOP']

        # If there are fewer STOP rows than START rows, there may be an extra START row
        if len(stops) < len(starts):
            print(f'({batch_cage}, {subject_id}) Number of STOPs is smaller than number of STARTs for {event_type}')
            
            # If the final row is an unpaired START, remove it
            if beh_dat_event.iloc[-1]['Behavior type'] == 'START':
                print('Removing last row because it is of type START')
                beh_dat_event = beh_dat_event.drop(beh_dat_event.index[-1])
            
            # Else, this behavior type is skipped because pairing is unclear.
            else:
                print(f'Number of STOPs is smaller than number of STARTs, but this is not caused by a START at '
                      f'the last row of the dataframe. Skipping..')
                continue
        
        # If there are fewer START rows than STOP rows, there may be an extra STOP row.
        if len(starts) < len(stops):
            print(f'({batch_cage}, {subject_id}) Number of STARTs is smaller than number of STOPs for {event_type}')
            
            # If the first row is an unpaired STOP, remove it
            if beh_dat_event.iloc[0]['Behavior type'] == 'STOP':
                print('Removing first row because it is of type STOP')
                beh_dat_event = beh_dat_event.drop(beh_dat_event.index[0])
            
            # Else, this behavior type is skipped because pairing is unclear.
            else:
                print(f'Number of STARTs is smaller than number of STOPs, but this is not caused by a STOP at '
                      f'the first row of the dataframe. Skipping..')
                continue
        
        # Merge paired START and STOP rows into one row per behavioral event.
        # This also calculates frame start, frame stop, and event duration.
        beh_dat_event = merge_event_rows(beh_dat_event)

        # Add subject-level metadata to the event dataframe
        beh_dat_event.insert(1, 'subject_id', subject_id)
        beh_dat_event.insert(2, 'genotype', genotype)

        # Add the cleaned events for this behavior type to the subject-level dataframe
        beh_df = pd.concat([beh_df, beh_dat_event], axis=0)

    return beh_df

def export_adjusted_fps_only():
    """
    Export adjusted FPS and synchronization information for each subject.

    This helper function calculates adjusted video FPS values from EEG TTL
    timestamps and LED onset frames, then saves a summary Excel file. It can be
    used independently when only the adjusted FPS summary is needed 
    (e.g. for behavioral trial time boundaries).

    Returns:
    ### fps_df [pandas.DataFrame]: Summary dataframe with subject metadata, adjusted FPS, sampling
        frequency, TTL counts, LED onset counts, and first/last sync events.
    """
    # Select the folder containing the NWB files.
    print('Select the folder holding your experiment NWB files')
    nwb_folder = select_folder("Select the folder holding your experiment NWB files")

    # Select the folder containing the video-analysis output
    print("Select the folder that holds the video analysis output")
    video_analysis_folder = select_folder("Select the folder that holds the video analysis output")

    # Select where the adjusted FPS summary Excel file should be saved
    print("Select folder where adjusted FPS Excel should be saved")
    output_folder = select_or_create_folder("Select output folder")

    # Store one summary row per successfully processed subject
    fps_rows = []

    # Loop through all NWB files
    for file in sorted(os.listdir(nwb_folder)):
        if not file.endswith(".nwb"):
            continue

        nwb_file_path = os.path.join(nwb_folder, file)

        # Open the NWB file and extract the subject metadata, TTL timestamps,
        # one filtered EEG channel, and the EEG sampling frequency.
        with NWBHDF5IO(nwb_file_path, "r") as io:
            nwb = io.read()

            subject_id = nwb.subject.subject_id
            genotype = nwb.subject.genotype

            # Skip this subject if the TTL_1 signal is missing.
            if "TTL_1" not in nwb.acquisition:
                print(f"Skipping {subject_id} — TTL_1 missing")
                continue
            
            # Read EEG TTL onset timestamps in seconds
            eeg_ttl_onsets_secs = list(nwb.acquisition["TTL_1"].timestamps)

            # At least two TTL events are needed to estimate adjusted FPS
            if len(eeg_ttl_onsets_secs) < 2:
                print(f"Skipping {subject_id} — only {len(eeg_ttl_onsets_secs)} EEG TTLs found")
                continue

            filtered_eeg = nwb.acquisition["filtered_EEG"].data[:].T[0]
            s_freq = nwb.acquisition["filtered_EEG"].rate

        # Match the NWB subject ID to the batch-cage identifier
        batch_cage = subject_id_batch_cage_dict.get(subject_id)

        if batch_cage is None:
            print(f"Skipping {subject_id} — not found in batch_cage dictionary")
            continue
        
        # Load LED onset frames for the matching video
        led_onsets = get_led_onsets(video_analysis_folder, batch_cage)

        # At least two LED onsets are needed to calculate adjusted FPS
        if len(led_onsets) < 2:
            print(f"Skipping {subject_id} / {batch_cage} — only {len(led_onsets)} LED onsets found")
            continue
        
        # Calculate the adjusted video FPS 
        adjusted_fps = adjust_fps(
            filtered_eeg,
            eeg_ttl_onsets_secs,
            led_onsets,
            s_freq,
            verbose=False
        )

        # Store subject metadata, adjusted FPS, and synchronization information
        fps_rows.append({
            "subject_id": subject_id,
            "batch_cage": batch_cage,
            "genotype": genotype,
            "nwb_file": file,
            "adjusted_fps": adjusted_fps,
            "sampling_frequency": s_freq,
            "n_eeg_ttls": len(eeg_ttl_onsets_secs),
            "n_led_onsets": len(led_onsets),
            "first_eeg_ttl_s": eeg_ttl_onsets_secs[0],
            "last_eeg_ttl_s": eeg_ttl_onsets_secs[-1],
            "first_led_onset_frame": led_onsets[0],
            "last_led_onset_frame": led_onsets[-1]
        })

        print(f"{subject_id} / {batch_cage}: adjusted FPS = {adjusted_fps:.4f}")

    # Convert all collected rows into a dataframe
    fps_df = pd.DataFrame(fps_rows)

    # Save the adjusted FPS summary as an Excel file
    output_file = os.path.join(output_folder, "adjusted_fps_summary_d2.xlsx")
    fps_df.to_excel(output_file, index=False)

    print(f"\nSaved adjusted FPS summary to: {output_file}")
    return fps_df

def main():
    """
    Run the Day 2 frame-based epoch creation pipeline.

    The user selects the NWB folder, EthoVision behavior folder, video-analysis
    folder, and output folder. For each NWB file, the script loads subject and
    EEG metadata, extracts behavior events, aligns video frames to EEG samples
    using adjusted FPS and TTL/LED synchronization, creates fixed-length epochs,
    and saves one epoch file per subject.
    """

    # select input and output folders
    print('Select the folder holding your experiment NWB files')
    nwb_folder = select_folder("Select the folder holding your experiment NWB files")
    print("Select the experiment's behaviour data folder")
    behaviour_data = select_folder("Select the experiment's behaviour data folder")
    print("Select the folder that holds the video analysis output (ROI Excel, pickle file)")
    video_analysis_folder = select_folder(
        "Select the folder that holds the video analysis output (ROI Excel, pickle file)")
    print("Select or create a folder to where the epoch files are saved")
    epochs_folder = select_or_create_folder("Select or create a folder to where the epoch files are saved")

    # Store information about subjects that are skipped during processing.
    skip_log = []

    # Loop through all NWB files in the selected folder.
    # One epoch file will be created per subject.
    for file in sorted(os.listdir(nwb_folder)):
        if not file.endswith(".nwb"):
            continue
        
        # check 
        if file == "3C_sociability_b2c4.3_backup.nwb": 
            print("found b2c4.3")
            subject_id =  "b2c4.3"
        
        nwb_file_path = os.path.join(nwb_folder, file)

        # Open the NWB file and extract subject information, EEG data,
        # sampling frequency, and TTL timestamps.
        with NWBHDF5IO(nwb_file_path, "r") as io:
            nwb = io.read()

            subject_id = nwb.subject.subject_id

            # Skip this subject if an epoch file already exists.
            if os.path.exists(os.path.join(epochs_folder, f'epochs_{subject_id}-epo.fif')):
                print(f'Epoch file epochs_{subject_id}-epo.fif already exists in the selected folder. Skipping..')
                continue
            
            # Load one filtered EEG channel to calculate adjusted FPS.
            filtered_eeg = nwb.acquisition['filtered_EEG'].data[:].T[0]  # only one channel needed to adjust the fps
            s_freq = nwb.acquisition['filtered_EEG'].rate  # sampling frequency/resampled frequency of the EEG
            eeg_ttl_onsets_secs = list(nwb.acquisition["TTL_1"].timestamps)  # timestamps of the TTL onsets in seconds
            
            # At least two TTL events are needed to calculate adjusted FPS.
            if len(eeg_ttl_onsets_secs) < 2:
                print(f"⚠️ Skipping {subject_id} — only {len(eeg_ttl_onsets_secs)} TTL found")
                skip_log.append({
                    "subject_id": subject_id,
                    "batch_cage": None,
                    "nwb_file": file,
                    "reason": f"{subject_id} — only {len(eeg_ttl_onsets_secs)} TTL found: no epochs created"
                })
                continue

            genotype = nwb.subject.genotype
            io.close()

        # get the batch_cage combination name to retrieve the correct behaviour data
        batch_cage = subject_id_batch_cage_dict.get(subject_id)
        if batch_cage is None:
            print(f"⚠️ Subject {subject_id} not found in batch_cage dictionary. Skipping.")
            skip_log.append({
                "subject_id": subject_id,
                "batch_cage": None,
                "nwb_file": file,
                "reason": "Subject {subject_id} not found in batch_cage dictionary.: No usable epochs created"
            })
            continue

        print(f'\nGetting {batch_cage}.xlsx file belonging to subject {subject_id}')
        print(f'Sampling frequency: {s_freq}')

        # Locate the EthoVision behavior file for this subject.
        file_path = os.path.join(behaviour_data, f'{batch_cage}.xlsx')

        # Skip if the behavior file is missing
        if not os.path.exists(file_path):
            print(f'⚠️  No behavior file found for {batch_cage}. Skipping subject {subject_id}.')
            skip_log.append({
                "subject_id": subject_id,
                "batch_cage": batch_cage if "batch_cage" in locals() else None,
                "nwb_file": file,
                "reason": f"No behavior file found for {batch_cage}. Skipping subject {subject_id}: No usable epochs created"
            })
            continue
        
        # Load and clean the EthoVision behavior data.
        cleaned = preprocess_behavior_excel(file_path)
        boris_like_df = convert_binary_to_event_rows(cleaned)
        beh_data = create_cleaned_event_df(boris_like_df, batch_cage, subject_id, genotype)

        print(f'Total number of events: {len(beh_data)}.')
        print(f'Number of events per type: {np.unique(beh_data["Behavior"], return_counts=True)}')

        # Optionally remove behavioral events that are shorter than the minimum duration
        if min_event_duration is not None:
            longer_than = len(beh_data[beh_data["Event duration"] >= min_event_duration])
            shorter_than = len(beh_data[beh_data["Event duration"] < min_event_duration])
            print(f'Percentage of events shorter than {min_event_duration} seconds: '
                  f'{shorter_than / (shorter_than + longer_than) * 100:.2f}%')

            beh_data = beh_data[beh_data["Event duration"] >= min_event_duration]
            beh_data.reset_index(drop=True, inplace=True)

        # get the LED states for this subject (i.e. get the LED states of the correct video)
        # and then get the frames where the LED turned ON (i.e. get all boolean event changes from OFF to ON (0 to 1)
        led_onsets = get_led_onsets(video_analysis_folder, batch_cage)

        # Skip the subject if there are not enough LED onsets for synchronization.
        if len(led_onsets) < 2:
            print(f"Skipping {subject_id} / {batch_cage} — only {len(led_onsets)} LED onsets found in video")
            skip_log.append({
                "subject_id": subject_id,
                "batch_cage": batch_cage if "batch_cage" in locals() else None,
                "nwb_file": file,
                "reason": f"Skipping {subject_id} / {batch_cage} — only {len(led_onsets)} LED onsets found in video: No usable epochs created"
            })
            continue

        # as the video isn't recorded at exactly 30 fps, we calculate the true fps
        # the offset here is the difference in TTL onset between the EEG and LED (negative means that LED has delay)
        adjusted_fps = adjust_fps(filtered_eeg, eeg_ttl_onsets_secs, led_onsets, s_freq, verbose=True) 
        
        # Calculate the time offset between the first EEG TTL and the first video LED onset
        first_ttl_offset = get_first_ttl_offset(eeg_ttl_onsets_secs, led_onsets, adjusted_fps) 

        # NOTE: DEBUG ALIGNMENT
        print(f"\n--- DEBUG ALIGNMENT for {subject_id} ---")
        print("Offset (sec):", first_ttl_offset)
        print("First EEG TTL (sec):", eeg_ttl_onsets_secs[0])
        print("First LED frame:", led_onsets[0])
        print("First LED (sec):", led_onsets[0] / adjusted_fps)
        print("--------------------------------------\n")

        # generate fixed length epochs
        all_epochs = get_epochs(nwb_file_path, beh_data, adjusted_fps, first_ttl_offset, s_freq, subject_id, genotype)
        if all_epochs is None:
            skip_log.append({
                "subject_id": subject_id,
                "batch_cage": batch_cage if "batch_cage" in locals() else None,
                "nwb_file": file,
                "reason": f"{subject_id} has empty epochs: No usable epochs created"
            })
            continue  # skip saving if no usable epochs

        # save this subject's epochs
        all_epochs.save(os.path.join(epochs_folder, f'epochs_{subject_id}-epo.fif'), overwrite=True)
        print(f'\nSuccessfully created and saved {len(all_epochs)} epochs for subject {subject_id}.')
    
    # Save a log of all skipped subjects, if any subjects were skipped.
    if len(skip_log) > 0:
        skip_df = pd.DataFrame(skip_log)

        csv_path = os.path.join(epochs_folder, "skipped_subjects_log.csv")
        xlsx_path = os.path.join(epochs_folder, "skipped_subjects_log.xlsx")

        skip_df.to_csv(csv_path, index=False)
        skip_df.to_excel(xlsx_path, index=False)

        print(f"\nSaved skipped-subject log to:")
        print(csv_path)
        print(xlsx_path)
    else:
        print("\nNo subjects were skipped.")

if __name__ == '__main__':
    main()
    # adjusted_fps_df = export_adjusted_fps_only() NOTE: if you only want fps
    print('\nDone!')