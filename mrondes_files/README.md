# mrondes_files

Reusable EEG, video-alignment, NWB, and epoching scripts originally written by Mirthe Ronde and her team, with some files later adjusted for this project.

This folder contains helper scripts used to prepare EEG data for the three-chamber social interaction project. The scripts support conversion from EDF to NWB, EEG filtering, LED/video synchronization, frame-based epoch creation for Day 2 and Day 3, and retrieval of EEG data from NWB files.

---

## Project context

These files are used in the analysis of social behavior and EEG activity in mice during a three-chamber paradigm.

The workflow connects three main data sources:

1. **EDF EEG recordings**
2. **EthoVision behavioral Excel files**
3. **experiment videos with LED synchronization pulses**

The main purpose of the code is to align behavioral events from video/EthoVision with EEG recordings, then create MNE-compatible EEG epochs for later PSD and connectivity analysis.

---

## Attribution

Most scripts in this folder were written by **M. Ronde and her team**.

Some files were adjusted (changes to functions + creation of new functions)
for this bachelor project, especially the scripts for:

- creating one NWB file at a time (based on Ronde's script to create NWB for a whole folder, I only needed
some files to be created, as most NWB files were provided)
- Day 2 sociability epoching
- Day 3 social recognition memory epoching
- small fixes to helper/retrieval functions

---

## Folder contents

```text
mrondes_files/
├── create_one_nwb_file.py
├── eeg_filter_functions.py
├── eeg_video_alignment_functions.py
├── frame_based_epochs_day2.py
├── frame_based_epochs_day3.py
├── granger_causality.py
├── helper_functions.py
├── identify_led_rois.py
├── nwb_retrieval_functions.py
├── settings_general.py
└── ttl_onset_extractor.py
```

---

## What each file does

| File | Purpose |
|---|---|
| `create_one_nwb_file.py` | Converts one EDF EEG recording into an NWB file. Adds subject metadata, electrode metadata, raw EEG, filtered EEG, and TTL synchronization events. |
| `eeg_filter_functions.py` | Contains EEG filtering functions, including interpolation of NaNs and artifact/package-loss handling. |
| `eeg_video_alignment_functions.py` | Contains functions for aligning EEG TTL pulses with video LED onsets and estimating the adjusted video FPS. |
| `frame_based_epochs_day2.py` | Creates Day 2 sociability EEG epochs from NWB files and EthoVision cup-investigation data. |
| `frame_based_epochs_day3.py` | Creates Day 3 social recognition memory EEG epochs from NWB files and EthoVision cup-investigation data. |
| `granger_causality.py` | Contains a Granger causality function. This method was not used in the current project. |
| `helper_functions.py` | Contains general helper functions for file selection, folder creation, EDF file discovery, and saving figures. |
| `identify_led_rois.py` | Lets the user select the LED region of interest in video frames and saves these ROIs to `video_rois.xlsx`. |
| `nwb_retrieval_functions.py` | Contains functions to retrieve raw/filtered EEG and package-loss information from NWB files. |
| `settings_general.py` | Contains project-wide settings, including subject IDs, batch-cage mappings, frequency bands, electrode information, filtering settings, and epoching settings. |
| `ttl_onset_extractor.py` | Extracts frame-by-frame LED on/off states from videos using the ROIs from `identify_led_rois.py` and saves them as `led_states.pickle`. |

---

## Visual workflow

```text
Raw EDF EEG files
        │
        ▼
create_one_nwb_file.py
        │
        ▼
NWB files with raw EEG, filtered EEG, metadata, and TTL events
        │
        ├───────────────┐
        │               │
        ▼               ▼
EthoVision Excel    Experiment videos
behavior files      with LED pulses
        │               │
        │               ▼
        │        identify_led_rois.py
        │               │
        │               ▼
        │        ttl_onset_extractor.py
        │               │
        │               ▼
        │        led_states.pickle
        │               │
        └───────┬───────┘
                ▼
eeg_video_alignment_functions.py
                │
                ▼
frame_based_epochs_day2.py / frame_based_epochs_day3.py
                │
                ▼
MNE epoch files: epochs_<subject_id>-epo.fif
                │
                ▼
Filtering of epochs: epochs_<subject_id>_cleaned-epo.fif
                │
                ▼
PSD and connectivity analysis notebooks
```

---

## Prerequisites

This code is written in Python and uses several scientific Python packages.

Recommended requirements:

- Python 3.10 or newer
- numpy
- pandas
- scipy
- matplotlib
- mne
- mne-connectivity
- pynwb
- ndx-events
- hdmf
- opencv-python
- openpyxl
- tkinter

Some scripts open graphical file-selection windows using `tkinter`, and some use OpenCV windows for selecting video ROIs. Therefore, these scripts should be run in an environment where graphical windows can open.

---

## Installation

Install the required packages:

```bash
pip install numpy pandas scipy matplotlib mne mne-connectivity pynwb ndx-events hdmf opencv-python openpyxl jupyter
```

If `tkinter` is missing, install it through your Python distribution or system package manager.

---

## Usage

Run scripts from the project root using `python -m`, so that imports between files work correctly.

### 1. Select LED ROIs from videos

Use this before extracting LED states.

```bash
python -m mrondes_files.identify_led_rois
```

This script asks you to select:

1. the folder containing the experiment videos
2. an output folder for the LED ROI file

Output:

```text
video_rois.xlsx
```

---

### 2. Extract LED states from videos

After creating `video_rois.xlsx`, run:

```bash
python -m mrondes_files.ttl_onset_extractor
```

This script asks you to select:

1. the folder containing `video_rois.xlsx`
2. the folder containing the experiment recordings

Output:

```text
led_states.pickle
```

This file stores the LED on/off state for every frame of each video.

---

### 3. Create one NWB file from one EDF recording

```bash
python -m mrondes_files.create_one_nwb_file
```

This script asks you to select:

1. the EDF file
2. the matching EthoVision Excel file
3. the output folder for the NWB file

Output example:

```text
3c_sociability_<subject_id>.nwb
```

The NWB file contains:

- subject metadata
- electrode metadata
- raw EEG
- filtered EEG
- TTL synchronization events

---

### 4. Create Day 2 frame-based epochs

Use this for **Day 2 sociability**.

```bash
python -m mrondes_files.frame_based_epochs_day2
```

This script asks you to select:

1. the folder containing NWB files
2. the Day 2 EthoVision behavior folder
3. the video-analysis output folder containing `led_states.pickle`
4. the output folder for epoch files

Output example:

```text
epochs_b1c1.1-epo.fif
```

Day 2 behavior labels:

- `with mouse cup`
- `without mouse cup`

These correspond to social and non-social interaction epochs.

---

### 5. Create Day 3 frame-based epochs

Use this for **Day 3 social recognition memory**.

```bash
python -m mrondes_files.frame_based_epochs_day3
```

This script asks for the same types of input folders as the Day 2 script.

Day 3 behavior labels:

- `novel cup`
- `familiar cup`

These correspond to investigation of the novel mouse and the familiar mouse.

---

## Important settings

Most project-wide settings are stored in:

```text
settings_general.py
```

This file includes:

- subject ID to batch-cage mappings
- EEG frequency bands
- filtering settings
- electrode/channel information
- frame-based epoching settings
- sex metadata dictionary

Commonly relevant settings include:

```python
filter_method = "mne"
resample_freq = None
package_loss_cutoff = 0.15
min_event_duration = None
desired_epoch_length = 1.0
overlap_epochs = False
epoch_overlap_cutoff = 0.5
```

EEG frequency bands used in the project:

```python
delta: 1-4 Hz
theta: 4-8 Hz
alpha: 8-13 Hz
beta: 13-30 Hz
gamma: 30-100 Hz
```

Recorded EEG channels include:

```text
AI_L, S1_L, A1_L, A1_R, ACA_R, AI_R, PMC_R, PCA_R
```

EMG channels are also present but not used in this project:

```text
EMG_L, EMG_R
```

---

## Expected inputs and outputs

### Inputs

Depending on the script, expected inputs include:

- `.edf` EEG recordings
- EthoVision `.xlsx` behavior files
- experiment video files, usually `.mp4` 
- `video_rois.xlsx`
- `led_states.pickle`
- `.nwb` files

### Outputs

The scripts can generate:

- `video_rois.xlsx`
- `led_states.pickle`
- `.nwb` files
- `epochs_<subject_id>-epo.fif`
- `skipped_subjects_log.csv`
- `skipped_subjects_log.xlsx`
- `adjusted_fps_summary_d2.xlsx`

---

## Notes on EEG-video alignment

The videos were theoretically recorded at 30 FPS, but the true frame rate can differ. The alignment scripts estimate an adjusted FPS by comparing EEG TTL pulses with video LED onsets.

The offset between EEG time and video time is then used to convert behavioral frame numbers into EEG sample indices.

This is necessary because the EEG recording and video recording do not start at exactly the same time.

---

## Troubleshooting

### Import errors

Run scripts from the project root with `python -m`, for example:

```bash
python -m mrondes_files.frame_based_epochs_day2
```

If you run scripts from inside the folder directly, imports such as `from settings_general import *` may fail depending on your working directory.

### Missing behavior file

Check whether the subject ID in the NWB file exists in `subject_id_batch_cage_dict` in `settings_general.py`, check whether the corresponding EthoVision file exists in the selected behavior folder, and check whether the video and EDF recording exists as well. 

### Missing LED onsets

Make sure that:

1. `identify_led_rois.py` was run first
2. `video_rois.xlsx` exists
3. `ttl_onset_extractor.py` was run successfully
4. `led_states.pickle` exists in the selected video-analysis folder
5. the video filename can be matched to the batch-cage identifier

### Not enough TTL pulses

At least two EEG TTL events and two video LED onsets are needed to estimate the adjusted FPS. Subjects with too few TTL/LED events are skipped.

### Empty epoch files or skipped events

Events may be skipped if:

- the aligned EEG start time is before the recording starts
- the EEG segment is empty
- the event is too short
- package loss exceeds the allowed cutoff
- START/STOP behavior rows cannot be paired correctly

Skipped subjects are saved in:

```text
skipped_subjects_log.csv
skipped_subjects_log.xlsx
```

---

## Notes

- `granger_causality.py` is included for completeness, but Granger causality was not a connectivity measure used in this project.
- Day 2 and Day 3 use similar epoching logic, but the behavior labels and EthoVision metadata rows differ.
- The current code uses interactive folder/file selection, so fully automated command-line execution is limited.
- Keep NWB files, video-analysis files, and epoch files in separate folders to avoid overwriting intermediate results.

---
