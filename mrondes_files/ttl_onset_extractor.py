"""
This file holds logic that extracts the state of the LED (on/off) in every frame
of all videos located in the given video folder. This LED state extraction is done
using the ROIs that are created using the identify_led_rois.py script.

To run: python -m mrondes.video_ttl_extraction.ttl_onset_extractor
"""

import ast
import cv2
import pickle
import pandas as pd
import numpy as np
import os

from helper_functions import *

def is_led_on(roi, threshold=245):
    """
    Returns True when the LED is on, False otherwise

    Parameters:
    ### roi [numpy.ndarray]: Image region containing the LED.
    ### threshold [int]: Pixel intensity threshold used to classify the LED as on.
        Default is 245.

    Returns:
    ### led_on [bool]: True if the LED is on, False otherwise.
    """
    return np.max(roi) >= threshold


def get_led_states(recordings_folder, rois_df):
    """
    For every row in the rois_df (holds the movie filename and roi info), the LED
    state is extracted and is stored. All saved info is later saved to a file.

    Parameters:
    ### recordings_folder [str]: Folder containing the experiment video recordings.
    ### rois_df [pandas.DataFrame]: Dataframe containing video filenames and ROI
        coordinates. It must include the columns "Video" and "ROI".

    Returns:
    ### all_led_states [dict]: Dictionary mapping each video filename to a NumPy
        array of LED states. Values are 1 when the LED is on and 0 when it is off.
    """

    all_led_states = {}

    # Loop through each video and its corresponding ROI
    for index, row in rois_df.iterrows():
        print(f"\nWorking with video {row['Video']}.")
        
        # Build full path to the video file
        video_path = os.path.join(recordings_folder, row['Video'])
        
        # Convert ROI string from the spreadsheet into a tuple/list
        roi = ast.literal_eval(row['ROI'])
        
        # Open video file
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        frame_number, prev_state = 0, 0
        states = []

        # Read video frame by frame
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Crop frame to the LED ROI.
            x, y, w, h = roi
            roi_frame = frame[y:y + h, x:x + w]
            
            # Classify LED state for this frame
            state = is_led_on(roi_frame)

            prev_state = state
            states.append(int(state))
            frame_number += 1

            # Print progress for the current video
            print('\r', f"{round(frame_number / total_frames * 100, 2)}% done..", end='')

        # Close the video file
        cap.release()
        all_led_states[row['Video']] = np.array(states)

    return all_led_states


def main():
    """
    Extract LED states from experiment videos and save them as a pickle file.
    
    This function asks the user to select the folder containing the
    video_rois.xlsx file and the folder containing the experiment recordings. It
    then loads the ROI table, extracts frame-by-frame LED states for each video,
    and saves the resulting dictionary as led_states.pickle.

    Returns:
    ### None: The function saves led_states.pickle in the selected video-analysis
        output folder.
    """
    print("Select the folder that holds the 'video_rois.xlsx' file")
    video_analysis_output_folder = select_or_create_folder("Select the folder that holds the 'video_rois.xlsx' file")
    print("Select the folder that holds the experiment recordings")
    recordings_folder = select_folder("Select the folder that holds the experiment recordings")

    # Load ROI table created during video ROI selection
    roi_df_path = os.path.join(video_analysis_output_folder, 'video_rois.xlsx')
    roi_df = pd.read_excel(roi_df_path)

    # Get LED states without saving any snapshots
    led_states = get_led_states(recordings_folder, roi_df)

    # Save LED state dictionary as a pickle file
    with open(os.path.join(video_analysis_output_folder, 'led_states.pickle'), "wb") as f:
        pickle.dump(led_states, f, pickle.HIGHEST_PROTOCOL)


if __name__ == '__main__':
    main()