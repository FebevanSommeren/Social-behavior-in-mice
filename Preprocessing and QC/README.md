# EEG Preprocessing and Quality Control

Helper scripts and notebooks for checking EEG/video alignment, correcting NWB metadata, and cleaning frame-based EEG epochs before PSD and connectivity analysis.

This folder contains quality-control and preprocessing tools used after the first frame-based epoch files have been created. The files are mainly used to inspect LED synchronization, generate adjusted trial boundaries for behavioral analyses, reject bad EEG epochs, and document rejected epochs.

---
## Project context

These files are part of the three-chamber social interaction project in mice. They support the EEG analysis pipeline by checking and cleaning data before final analyses.

The main pipeline is:

```text
NWB files
   │
   ▼
frame-based epoch files
   │
   ▼
alignment checks and adjusted timing checks
   │
   ▼
epoch rejection / cleaning
   │
   ▼
cleaned epoch files
   │
   ▼
PSD and connectivity analysis
```

This folder is not the main analysis folder. Instead, it contains supporting files used to make sure the epoch files are correct and clean enough for later EEG analyses.

---

## Folder contents

```text
eeg_preprocessing_qc/
├── README.md
├── adjusted_experimental_periods.ipynb
├── bad_epochs_report.txt
├── changing_id_nwb.py
├── check_led_states.ipynb
├── epoch_rejection.py
└── ptp_summary_d2_run2.csv
```

---

## What each file does

| File | Description |
|---|---|
| `adjusted_experimental_periods.ipynb` | Creates the `ANIMAL_TRIAL_TIME_BOUNDARIES` dictionary used in behavioral analyses. It uses the adjusted FPS summary file created during frame-based epoching and converts first/last LED frames into trial start and end times. |
| `check_led_states.ipynb` | Inspects the `led_states.pickle` file. It checks LED on/off values per video and helps verify whether LED onset detection worked correctly. |
| `epoch_rejection.py` | Cleans MNE epoch files. It renames channels, sets montage information, detects flat signal segments, rejects high and low peak-to-peak epochs, and saves cleaned epoch files. |
| `bad_epochs_report.txt` | Text report listing bad windows found in epochs, including timing and affected channels. Created via `epoch_rejection.py`. |
| `ptp_summary_d2_run2.csv` | Summary table of peak-to-peak amplitude values for Day 2 run 2 epoch files. Used to inspect amplitude ranges and possible rejection thresholds. Created via `epoch_rejection.py`. |
| `changing_id_nwb.py` | Special-case script for correcting an incorrect subject ID and description inside an NWB file. It creates a backup before editing. |

---

## Prerequisites

Recommended software and Python packages:

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- numpy
- pandas
- matplotlib
- mne
- pynwb
- h5py
- openpyxl

The scripts also depend on functions and settings from the `mrondes_files` folder, especially:

```text
mrondes_files.helper_functions
mrondes_files.settings_general
mrondes_files.eeg_filter_functions
```

Make sure `mrondes_files` is available in the same project environment.

---

## Installation

Install the required packages:

```bash
pip install numpy pandas matplotlib mne pynwb h5py openpyxl jupyter
```

Then start Jupyter:

```bash
jupyter notebook
```

or:

```bash
jupyter lab
```

---

## Usage

### 1. Check LED states

Open:

```text
check_led_states.ipynb
```

Use this notebook to inspect the LED state pickle file created from the video recordings.

Input:

```text
led_states.pickle
```

Main checks:

- list all video keys in the pickle file
- inspect one video entry
- check the first LED states
- plot LED states over time
- identify whether LED detection looks reasonable

This is useful before using LED onsets for EEG/video alignment.

---

### 2. Create adjusted experimental period boundaries

Open:

```text
adjusted_experimental_periods.ipynb
```

This notebook creates a dictionary called:

```python
ANIMAL_TRIAL_TIME_BOUNDARIES
```

The notebook uses an adjusted FPS summary file, usually created by `export_adjusted_fps_only()` from the frame-based epoching scripts.

Expected input columns include:

```text
batch_cage
adjusted_fps
first_led_onset_frame
last_led_onset_frame
```

Output example:

```text
animal_trial_time_boundaries_day2.txt
```

This output can be copied into the Day 2 or Day 3 behavioral analysis notebooks.

---

### 3. Summarize peak-to-peak amplitudes

The file:

```text
ptp_summary_d2_run2.csv
```

contains peak-to-peak amplitude summaries for Day 2 run 2 epoch files.

It includes columns such as:

```text
subject_id
file
n_epochs
lowest_epoch_ptp_uv
highest_epoch_ptp_uv
median_lowest_ptp_uv
median_highest_ptp_uv
p1_lowest_ptp_uv
p99_highest_ptp_uv
p5_lowest_ptp_uv
p95_highest_ptp_uv
```

This file is the output of `find_high_and_low_ptp_all_files` function and can be used together with `summary_ptps` to inspect
the full summary table, identify the subjects/files with the highest and lowest peak-to-peak values, and calculates the average of the 10 most extreme high and low PTP values.

---

### 4. Clean epoch files

The main script for epoch cleaning is:

```text
epoch_rejection.py
```

This script can be used to clean one file for testing or to batch-process a folder of epoch files.

Main cleaning steps:

1. Rename channels using the correct batch-specific electrode configuration.
2. Select EEG channels and exclude EMG channels.
3. Detect epochs with flat signal windows.
4. Reject epochs with high peak-to-peak amplitude.
5. Reject epochs with low peak-to-peak amplitude.
6. Save cleaned epoch files.
7. Print and save rejection summaries.

The script contains helper functions including:

```python
test_one_file()
find_high_and_low_ptp_all_files()
summary_ptps()
check_bad_epoch_percentage()
```

Example use inside Python:

```python
from epoch_rejection import test_one_file

epochs_clean, rejected_epochs = test_one_file(
    input_path="frame based epochs d2 run2/epochs_b1c1.1-epo.fif",
    output_folder="necessary epoch files d2"
)
```

The cleaned output file is saved with a suffix such as:

```text
-cleaned-epo.fif
```

---

### 5. Correct an NWB subject ID

Use this only for the special case where an NWB file contains an incorrect subject ID or description.

Run:

```bash
python changing_id_nwb.py
```

or import the function:

```python
from changing_id_nwb import update_nwb_subject_id

update_nwb_subject_id(
    nwb_path="3C_sociability_b2c4.3 (1).nwb",
    new_subject_id="b2c4.3"
)
```

The script creates a backup copy before editing the NWB file.

---

## Expected inputs

Depending on the file, expected inputs include:

- `led_states.pickle`
- adjusted FPS summary Excel files
- frame-based MNE epoch files, for example `epochs_<subject_id>-epo.fif`
- NWB files
- peak-to-peak summary CSV files

---

## Expected outputs

The files in this folder can produce:

- `animal_trial_time_boundaries_day2.txt`
- cleaned epoch files, for example `epochs_<subject_id>-cleaned-epo.fif`
- peak-to-peak summary CSV files
- bad epoch reports
- rejection summaries
- backup NWB files when subject IDs are corrected

---

## Notes

- This folder is mainly for preprocessing and quality control
- Run LED checks before relying on adjusted FPS or trial boundaries.
- Keep raw frame-based epochs separate from cleaned epochs.
- Use the same subject IDs across behavioral, EEG, and NWB files.
- Be careful when using `changing_id_nwb.py`, because it edits NWB metadata in place. Always keep the backup file.
- Some files are exploratory or diagnostic and may not need to be rerun for every analysis.

---

## Troubleshooting

### `mrondes_files` import error

Make sure the project root is the current working directory, and that `mrondes_files` is available.

Example:

```bash
cd path/to/project/root
python -m eeg_preprocessing_qc.epoch_rejection
```

If the folder is not a Python package, run functions from a notebook or update the import paths.

### No LED onsets found

Check that:

1. the correct `led_states.pickle` file was selected
2. the LED ROI was selected correctly
3. the LED threshold was appropriate
4. the video filename matches the expected subject or batch-cage identifier

### Too many epochs are rejected

Inspect:

- the bad epoch plots
- `bad_epochs_report.txt`
- peak-to-peak summary values
- flat-signal thresholds
- high/low PTP thresholds


### Subject ID mismatch

Check:

- NWB subject metadata
- epoch file names
- behavioral file names
- `subject_id_batch_cage_dict` in `settings_general.py`

Use `changing_id_nwb.py` only when the NWB metadata itself is incorrect (very rare case)

---
