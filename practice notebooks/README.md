# Practice Notebooks

Practice notebooks for learning how to work with EEG data, MNE-Python, and NWB files before applying these tools to the main three-chamber social interaction project.

This folder is mainly for exploration and learning. The notebooks are not part of the final analysis pipeline, but they document useful first steps for understanding EEG preprocessing, plotting, epoching, and inspecting NWB file structure.

---

## Folder contents

```text
practice notebooks/
├── README.md
├── eeg_mne_practice.ipynb
└── reading_nwb_file.ipynb
```

---

## What each notebook does

| Notebook | Description |
|---|---|
| `eeg_mne_practice.ipynb` | Practice notebook for learning basic MNE-Python functionality using an example EEG dataset. It covers loading data, plotting EEG signals, plotting power spectral density, resampling, filtering, notch filtering, finding/creating events, creating epochs, and selecting/plotting epochs. |
| `reading_nwb_file.ipynb` | Practice notebook for opening and inspecting a Neurodata Without Borders (NWB) file. It checks top-level NWB contents, subject metadata, raw EEG, filtered EEG, timestamps, TTL events, and electrode information. |

---

## Project context

The main project uses EEG recordings, behavioral data, and NWB files to study social behavior in mice.

These notebooks were used to become familiar with:

- the MNE workflow for EEG data
- basic EEG preprocessing concepts
- raw and epoched EEG objects
- plotting EEG signals
- inspecting PSDs
- reading NWB files
- checking raw EEG, filtered EEG, TTL events, and metadata stored inside NWB files


---

## Prerequisites

Recommended software and packages:

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- numpy
- matplotlib
- mne
- pynwb

The `reading_nwb_file.ipynb` notebook also uses the `select_file` helper function from:

```text
mrondes_files/helper_functions.py
```

Make sure the `mrondes_files` folder is available in the same project environment. 

---

## Installation

Install the required packages:

```bash
pip install numpy matplotlib mne pynwb jupyter
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

### 1. Practice basic EEG analysis with MNE

Open:

```text
eeg_mne_practice.ipynb
```

This notebook uses an example dataset from MNE and walks through basic EEG analysis steps.

Topics covered:

1. importing MNE and numpy
2. loading an example dataset
3. selecting EEG channels
4. plotting raw EEG
5. plotting power spectral density
6. resampling EEG data
7. high-pass filtering
8. low-pass filtering
9. notch filtering
10. finding events
11. creating fixed-length events
12. creating MNE `Epochs`
13. selecting and plotting epochs

---

### 2. Practice reading an NWB file

Open:

```text
reading_nwb_file.ipynb
```

This notebook lets you select an NWB file and inspect what is inside it.

It checks:

- acquisition objects
- processing objects
- devices
- electrode groups
- subject ID
- sex
- genotype
- raw EEG object
- filtered EEG object
- data shape
- sampling rate
- timestamps
- TTL events
- electrode table information

This is useful for checking whether an NWB file contains the expected EEG data and metadata before using it in later scripts.

---

## Expected inputs

### `eeg_mne_practice.ipynb`

This notebook downloads or loads an MNE example dataset automatically using:

```python
mne.datasets.sample.data_path()
```

No project-specific input files are required.

### `reading_nwb_file.ipynb`

This notebook expects one NWB file selected by the user.

Example input:

```text
3C_sociability_<subject_id>.nwb
```

---

## Expected outputs

These notebooks are mainly exploratory and do not produce final analysis output files by default.

---

## Notes

- These notebooks are for practice and learning, not final analysis.
- Results from these notebooks should not be treated as final project results.
- The MNE practice notebook uses an example dataset, not the project mouse EEG recordings.

---
