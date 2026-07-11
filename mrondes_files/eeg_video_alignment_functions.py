"""
This file holds general, reusable eeg epoching functions
MIRTHE RONDE 
"""

import numpy as np

def get_first_ttl_offset(eeg_ttl_onsets, led_ttl_onsets, adjusted_fps): 
    """
    Calculates an offset we use to align the EEG and the video data. This is needed because the video recording and the
    EEG recording didn't start at exactly the same moment, so we have to align the two data sources. we calculate the
    offset in seconds between the first EEG TTL and video LED TTL onset.

    Parameters:
    ### eeg_ttl_onsets [array-like]: EEG TTL onset times in seconds.
    ### led_ttl_onsets [array-like]: Video LED onset frame numbers.
    ### adjusted_fps [float]: Adjusted video frame rate used to convert frames
        to seconds.

    Returns:
    ### offset_secs [float]: Offset in seconds between EEG and video time.
    """
    # scale back to seconds using adjusted FPS
    first_led_onset_secs = led_ttl_onsets[0] / adjusted_fps  

    # get the offset
    offset_secs = eeg_ttl_onsets[0] - first_led_onset_secs  

    return offset_secs


def get_ttl_offset(eeg_ttl_onsets, led_ttl_onsets, adjusted_fps):
    """
    Function added 
    Calculate EEG-video offset using multiple TTL events instead of only the first one.
    Returns offset in seconds.

    Parameters:
    ### eeg_ttl_onsets [array-like]: EEG TTL onset times in seconds.
    ### led_ttl_onsets [array-like]: Video LED onset frame numbers.
    ### adjusted_fps [float]: Adjusted video frame rate used to convert video
        frames to seconds.

    Returns:
    ### offset_secs [float]: Median offset in seconds between EEG and video time.
    """
    # Convert input arrays to NumPy arrays
    eeg_ttl_onsets = np.asarray(eeg_ttl_onsets)
    led_ttl_onsets = np.asarray(led_ttl_onsets)

    # Use only the number of TTL events available in both signals
    n = min(len(eeg_ttl_onsets), len(led_ttl_onsets))

    if n == 0:
        raise ValueError("No TTL/LED onsets available to calculate offset.")

    if n < 2:
        print("⚠️ Only one TTL pair found. Using first TTL only.")

    # Keep matched TTL/LED pairs only
    eeg_ttl_onsets = eeg_ttl_onsets[:n]

    # convert frames to seconds
    led_ttl_secs = led_ttl_onsets[:n] / adjusted_fps

    # Get offsets 
    offsets = eeg_ttl_onsets - led_ttl_secs

    # Use median offset for robustness against outliers
    offset_secs = np.median(offsets)

    print(f"Offset based on {n} TTL pairs: {offset_secs:.4f} sec")
    print(f"Offset variation: {np.std(offsets):.4f} sec")

    return offset_secs

def adjust_fps(eeg_signal, eeg_ttl_onsets, led_ttl_onsets, s_freq, verbose=True):
    """
    The experiment videos were recorded in 30 fps, thus, in theory the amount of frames in one second should be 30.
    However, the true framerate of the recordings seems to be lower. Therefore, we need to adjust the fps and know
    the offset to correctly align the behavioural data (time-stamped using frame numbers) and the EEG data.

    We return the adjusted fps, which is used to account for the video lacking behind (not exactly 30 FPS), and we
    return the offset between the first EEG TTL and the first LED ttl, as both recordings didn't start at the exact
    same time. This offset is used to align the data.

    Parameters:
    ### eeg_signal [numpy.ndarray]: EEG signal used to determine the number of
        samples between the first and last EEG TTL pulses.
    ### eeg_ttl_onsets [array-like]: EEG TTL onset times in seconds.
    ### led_ttl_onsets [array-like]: Video LED onset frame numbers.
    ### s_freq [float]: EEG sampling frequency in Hz.
    ### verbose [bool]: Whether to print timing information. Default is True.

    Returns:
    ### adjusted_fps [float]: Estimated true video frame rate.
    """
    # find length of eeg signal between the two pulse combination (i.e. the number of samples between the two pulses)
    eeg_len = eeg_signal[int(s_freq * eeg_ttl_onsets[0]): int(s_freq * eeg_ttl_onsets[-1])].shape[0]

    if verbose:
        print(f'There are {eeg_len} EEG samples between the first and last TTL pulses, '
              f'which translates to {eeg_len / s_freq} seconds and {eeg_len / s_freq / 60} minutes of data')

    # find length of video frames between the two pulse combination
    frame_len = led_ttl_onsets[-1] - led_ttl_onsets[0]

    if verbose:
        print(f'There are {frame_len} frames between the first and last LED pulses, which theoretically equals'
              f' to {frame_len / 30} seconds and {frame_len / 30 / 60} minutes of data')

    # there are fewer frames between the two LED pulses than there should be, so the camera isn't recording at exactly
    # the theoretical 30 frames per second.

     # 🪵 Debug prints
    print(f"➡️  Debug: frame_len = {frame_len}, eeg_len = {eeg_len}, s_freq = {s_freq}")
    # print(f"➡️  EEG TTL onset timestamps: {eeg_ttl_onsets}")

    # therefore, we adjust the fps using the time spent between the two EEG TTL pulses (we assume this to be correct)
    # so, we divide the number of EEG samples recorded between the two pulses by the sampling freq to get the time spent
    # in seconds between those pulses, and we then calculate the true FPS by dividing the recorded frames by this value
    if eeg_len == 0:
        raise ValueError("EEG segment has zero length — cannot compute adjusted FPS. Check TTL alignment.")
    adjusted_fps = frame_len / (eeg_len / s_freq)


    if verbose:
        print(f'Adjusted FPS: {adjusted_fps}. Total frames / adjusted_fps = {frame_len / adjusted_fps} seconds. '
              f'That value should be equal to EEG samples / sampling_frequency: {eeg_len / s_freq}.')

    return adjusted_fps