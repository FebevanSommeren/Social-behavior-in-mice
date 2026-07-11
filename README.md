# Social Behavior and EEG Analysis in Alzheimer’s Disease Mice

Analysis project for investigating sociability, social recognition memory, and related EEG activity in pre-pathological 3xTg-AD mice and non-transgenic control mice using a three-chamber social interaction paradigm.

This repository contains behavioral analysis notebooks, EEG power spectral density and connectivity notebooks, NWB/epoching utilities, quality-control scripts, and practice notebooks used during the project.

---

## Project overview

This bachelor project investigates early behavioral and neural differences in a triple-transgenic mouse model of Alzheimer’s disease (3xTg AD).

The main experimental groups are:

- pre-pathological 3xTg-AD mice
- non-transgenic control mice

Both male and female mice are included.

The experiment uses a three-chamber paradigm across three days:

```text
Day 1: Habituation
Day 2: Sociability
Day 3: Social recognition memory
```

The main analyses focus on:

1. behavioral preference scores from EthoVision output
2. EEG power spectral density analysis
3. EEG functional connectivity analysis

---

## Research questions
The repository is used to answer the research questions of the project: 

1. *What are the differences in sociability, social recognition memory, and related neural activity in default mode network-associated brain regions between pre-pathological 3xTg Alzheimer’s disease mice and non-transgenic control mice in a three-chamber paradigm?*

2. *What are the differences between sexes?*

---

## Repository structure

```text
project-root/
├── README.md
├── Day 2 - sociability/
│   ├── README.md
│   ├── Behavioral analysis/
│   │   └── behavioral_analysis_day2.ipynb
│   ├── EEG analysis/
│   │   ├── psd_analysis_day2.ipynb
│   │   └── con_analysis_day2.ipynb
│   ├── frame based epochs d2/
│   └── filtered epochs d2/
├── Day 3 - social recognition memory/
│   ├── Behavioral analysis/
│   ├── EEG analysis/
│   ├── frame based epochs d3/
│   └── filtered epochs d3/
├── mrondes_files/
│   ├── README.md
│   ├── create_one_nwb_file.py
│   ├── eeg_filter_functions.py
│   ├── eeg_video_alignment_functions.py
│   ├── frame_based_epochs_day2.py
│   ├── frame_based_epochs_day3.py
│   ├── helper_functions.py
│   ├── identify_led_rois.py
│   ├── nwb_retrieval_functions.py
│   ├── settings_general.py
│   └── ttl_onset_extractor.py
├── Preprocessing and QC/
│   ├── README.md
│   ├── adjusted_experimental_periods.ipynb
│   ├── check_led_states.ipynb
│   ├── epoch_rejection.py
│   ├── changing_id_nwb.py
│   ├── bad_epochs_report.txt
│   └── ptp_summary_d2_run2.csv
└── practice notebooks/
    ├── README.md
    ├── eeg_mne_practice.ipynb
    └── reading_nwb_file.ipynb
```

---

## Main folders

### `Day 2 - sociability/`

Contains the analysis for Day 2 of the three-chamber paradigm.

On Day 2, the test mouse explores:

- a cup containing a novel mouse
- an empty cup

The behavioral analysis calculates a sociability or discrimination index:

$
SI = \frac{t_{social} - t_{non-social}}{t_{social} + t_{non-social}}
$

The EEG analysis uses Day 2 epochs for:

- PSD analysis
- connectivity analysis

Main comparison:

```text
with mouse cup vs without mouse cup
```

---

### `Day 3 - social recognition memory/`

Contains the analysis for Day 3 of the three-chamber paradigm.

On Day 3, the test mouse explores:

- the familiar mouse from Day 2
- a novel mouse

The behavioral analysis calculates a social novelty index:

$
SNI = \frac{t_{novel} - t_{familiar}}{t_{novel} + t_{familiar}}
$

The EEG analysis can compare activity during:

```text
novel cup vs familiar cup
```

---

### `mrondes_files/`

Contains reusable scripts originally written by Mirthe Ronde and her team, with some files later adjusted for this project.

This folder includes code for:

- converting EDF recordings to NWB files
- filtering EEG data
- extracting LED states from videos
- aligning video frames with EEG samples
- creating frame-based Day 2 and Day 3 EEG epochs
- retrieving data from NWB files
- storing general project settings

Important scripts:

```text
frame_based_epochs_day2.py
frame_based_epochs_day3.py
settings_general.py
```

---

### `Preprocessing and QC/`

This folder contains support files for checking and cleaning data before final EEG analyses.

It includes:

- LED-state checking
- adjusted experimental period boundaries
- NWB subject-ID correction
- epoch rejection and cleaning
- peak-to-peak amplitude summaries
- bad epoch reports

The main cleaning script is:

```text
epoch_rejection.py
```

---

### `practice notebooks/`

Contains exploratory notebooks used for learning and testing.

These notebooks are not part of the final analysis pipeline.

They include:

- practice with MNE-Python
- reading and inspecting NWB files
- checking EEG objects, TTL events, metadata, and acquisitions

---

## Analysis workflow

The overall workflow is:

```text
1. Raw EDF EEG files + EthoVision files + videos
        │
        ▼
2. Select LED ROIs and extract LED states
        │
        ▼
3. Convert EDF files to NWB files
        │
        ▼
4. Align EEG and video using TTL/LED synchronization
        │
        ▼
5. Create frame-based MNE epochs for Day 2 and Day 3
        │
        ▼
6. Inspect and clean epochs
        │
        ▼
7. Run behavioral analyses
        │
        ▼
8. Run EEG PSD analyses
        │
        ▼
9. Run EEG connectivity analyses
        │
        ▼
10. Compare genotype, sex, behavior, and EEG measures
```

---

## Prerequisites

Recommended software:

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- a working graphical Python environment for scripts that use file-selection windows or OpenCV ROI selection

Recommended Python packages:

```text
numpy
pandas
scipy
matplotlib
seaborn
statsmodels
mne
mne-connectivity
pynwb
ndx-events
hdmf
h5py
opencv-python
openpyxl
jupyter
```

---

## Installation

Install the main dependencies:

```bash
pip install numpy pandas scipy matplotlib seaborn statsmodels mne mne-connectivity pynwb ndx-events hdmf h5py opencv-python openpyxl jupyter
```

Start Jupyter:

```bash
jupyter notebook
```

or:

```bash
jupyter lab
```

---

## How to use this repository

### 1. Start with the practice notebooks if needed

Use these notebooks to understand the tools:

```text
practice notebooks/eeg_mne_practice.ipynb
practice notebooks/reading_nwb_file.ipynb
```

These are optional and mainly for learning.

---

### 2. Prepare NWB files and synchronization files

Use the scripts in:

```text
mrondes_files/
```

Typical order:

```bash
python -m mrondes_files.identify_led_rois
python -m mrondes_files.ttl_onset_extractor
python -m mrondes_files.create_one_nwb_file
```

The first two scripts create LED synchronization files from videos. The NWB creation script creates NWB files containing raw EEG, filtered EEG, subject metadata, electrode metadata, and TTL events.

---

### 3. Create frame-based EEG epochs

For Day 2:

```bash
python -m mrondes_files.frame_based_epochs_day2
```

For Day 3:

```bash
python -m mrondes_files.frame_based_epochs_day3
```

These scripts align EthoVision behavior periods with EEG data and save MNE epoch files.

Example output:

```text
epochs_<subject_id>-epo.fif
```

---

### 4. Check and clean epochs

Use:

```text
Preprocessing and QC/epoch_rejection.py
```

This script can detect and remove:

- flat epochs
- epochs with high peak-to-peak amplitude
- epochs with low peak-to-peak amplitude

Cleaned files should be saved separately from the original frame-based epochs.

---

### 5. Run Day 2 analysis

Open the notebooks in:

```text
Day 2 - sociability/
```

Recommended order:

```text
Behavioral analysis/behavioral_analysis_day2.ipynb
EEG analysis/psd_analysis_day2.ipynb
EEG analysis/con_analysis_day2.ipynb
```

---

### 6. Run Day 3 analysis

Open the notebooks in:

```text
Day 3 - social recognition memory/
```

Recommended order:

```text
Behavioral analysis/
EEG analysis/
```

Run the behavioral analysis first, then EEG PSD/connectivity analyses.

---

## Main behavioral measures

### Day 2: Sociability index

$
SI = \frac{t_{social} - t_{non-social}}{t_{social} + t_{non-social}}
$

Interpretation:

- `1` = preference for the social stimulus
- `0` = no preference
- `-1` = preference for the non-social stimulus

### Day 3: Social novelty index
$
SNI = \frac{t_{novel} - t_{familiar}}{t_{novel} + t_{familiar}}
$

Interpretation:

- `1` = preference for the novel mouse
- `0` = no preference
- `-1` = preference for the familiar mouse

---

## Main EEG analyses

### Power spectral density

PSD analysis compares spectral power across:

- genotype
- sex
- interaction kind
- frequency band

Frequency bands used in the project include:

```text
delta: 1-4 Hz
theta: 4-8 Hz
alpha: 8-13 Hz
beta: 13-30 Hz
gamma: 30-100 Hz
```

### Connectivity

Connectivity analysis compares functional connectivity across:

- genotype
- sex
- interaction kind
- frequency band

Connectivity measures include:

```text
wpli2_debiased
dpli
```

Special interest is given to DMN-related channels:

```text
ACA_R
PCA_R
```

---

## Important notes

- Do not mix Day 2 and Day 3 behavioral files or epoch files.
- Keep raw data, frame-based epochs, cleaned epochs, and final outputs in separate folders.
- Use consistent subject IDs across NWB files, EthoVision files, epoch files, and analysis outputs.
- Check LED synchronization before relying on adjusted frame-to-EEG alignment.
- Check epoch quality before using epochs in PSD or connectivity analysis.

---

## Expected outputs

Depending on which scripts and notebooks are run, outputs may include:

```text
video_rois.xlsx
led_states.pickle
*.nwb
epochs_<subject_id>-epo.fif
epochs_<subject_id>-cleaned-epo.fif
skipped_subjects_log.csv
skipped_subjects_log.xlsx
adjusted_fps_summary_d2.xlsx
animal_trial_time_boundaries_day2.txt
ptp_summary_*.csv
behavioral summary tables
PSD result tables and plots
connectivity result tables and plots
```
---

## Troubleshooting

### Import errors

Run scripts from the project root using `python -m`.

Example:

```bash
python -m mrondes_files.frame_based_epochs_day2
```

### Missing behavior files

Check that the selected behavior folder contains the expected EthoVision Excel files and that the subject ID can be matched to the batch-cage dictionary in `settings_general.py`.

### Missing LED onsets

Check that:

1. LED ROIs were selected correctly
2. `video_rois.xlsx` exists
3. `ttl_onset_extractor.py` was run successfully
4. `led_states.pickle` exists
5. video filenames match the expected batch-cage identifiers

### Too many rejected epochs

Inspect:

- bad epoch plots
- peak-to-peak summary files
- bad epoch reports
- flat-signal thresholds
- high/low PTP thresholds

### NWB subject ID mismatch

Use the NWB inspection notebook first. Only use the NWB subject-ID correction script if the NWB metadata itself is incorrect.

---

## Attribution

Project-specific analysis and adaptations were written for this bachelor project.

Several helper scripts in `mrondes_files/` were originally written by **Mirthe Ronde and her team**. Some of these files were partly adjusted for this project.

---