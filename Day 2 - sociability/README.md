# Day 2 - Sociability

This folder contains the analysis pipeline for **Day 2 of the three-chamber social interaction paradigm**, which tests **sociability** in pre-pathological 3xTg-AD mice and non-transgenic control mice.

On Day 2, each mouse explores a three-chamber arena containing:

- one cup with a mouse: the **social stimulus**
- one empty cup: the **non-social stimulus**

The main goal is to quantify how much time the test mouse spends investigating the social stimulus compared with the empty cup, and to analyze EEG activity during those same behaviorally defined interaction periods.

---

## Folder structure

```text
Day 2 - sociability/
├── __init__.py
├── README.md
├── Behavioral analysis/
│   └── behavioral_analysis_day2.ipynb
├── EEG analysis/
│   ├── psd_analysis_day2.ipynb
│   └── con_analysis_day2.ipynb
├── filtered epochs d2/
└── frame based epochs d2/
```
---
## Prerequisites

This analysis uses Python and Jupyter notebooks.

Recommended setup:

- Python 3.10 or newer
- Jupyter Notebook or JupyterLab
- pandas
- numpy
- matplotlib
- seaborn
- scipy
- statsmodels
- mne
- mne-connectivity

---

## Installation

Install the required packages:

```bash
pip install pandas numpy matplotlib seaborn scipy statsmodels mne mne-connectivity jupyter
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

Run the notebooks in this order.

## Behavioral analysis

The behavioral analysis uses EthoVision output files from Day 2 to calculate sociability-related measures.

The main notebook is:

```text
behavioral_analysis_day2.ipynb
```

This notebook:

1. Loads and processes Day 2 EthoVision Excel files.
2. Extracts time spent investigating the cup with the mouse and the empty cup.
3. Calculates total investigation time.
4. Calculates the sociability/discrimination index.
5. Visualizes sociability measures by genotype and sex.
6. Performs statistical analyses, including assumption checks and two-way ANOVAs.

### Sociability / discrimination index

Sociability is quantified using:

$
SI = \frac{t_{social} - t_{non-social}}{t_{social} + t_{non-social}}
$

where:

- `t_social` = time spent investigating the cup containing the mouse
- `t_non-social` = time spent investigating the empty cup

The index ranges from `-1` to `1`:

- `1` = exclusive preference for the social stimulus
- `0` = no preference 
- `-1` = exclusive preference for the non-social stimulus

---

## EEG analysis

The EEG analysis uses Day 2 epochs that were created from behaviorally relevant interaction periods.

For Day 2, the relevant EEG conditions are:

- **with mouse cup**: epochs when the test mouse investigates the social stimulus
- **without mouse cup**: epochs when the test mouse investigates the empty/non-social cup

The EEG analysis consists of two main parts:

1. **Power spectral density (PSD) analysis**
2. **Connectivity analysis**

---

## PSD analysis

The main notebook is:

```text
psd_analysis_day2.ipynb
```

This notebook analyzes spectral power during Day 2 sociability epochs.

It includes:

1. Loading subject-level Day 2 epochs.
2. Checking the number of subjects and epoch distribution.
3. Calculating subject-wise PSD summaries.
4. Checking for outliers and visually inspecting flagged subjects.
5. Plotting normalized PSDs across subjects, genotype, sex, and interaction type.
6. Calculating the PSD ratio between social and non-social interaction epochs.
7. Adding frequency-band labels.
8. Calculating band-wise PSD ratios per subject.
9. Performing independent-samples t-tests.
10. Applying FDR correction where relevant.

The main comparison is across:
- genotype: `3xTg` vs `Ntg`
- sex: male vs female
- EEG frequency bands

Relevant EEG channels used in the notebook include:

```text
AI_L, S1_L, A1_L, A1_R, ACA_R, AI_R, PMC_R, PCA_R
```

The DMN-related channels of interest are:

```text
ACA_R, PCA_R
```

---

## Connectivity analysis

The main notebook is:

```text
con_analysis_day2.ipynb
```

This notebook analyzes functional connectivity during Day 2 sociability epochs.

The main connectivity measures are:

- `wpli2_debiased`: debiased squared weighted phase-lag index
- `dpli`: directed phase-lag index

The notebook includes:

1. Loading subject-level Day 2 epochs.
2. Defining relevant EEG channels.
3. Calculating connectivity for social and non-social interaction epochs.
4. Plotting genotype and sex differences in connectivity.
5. Calculating channel-pair connectivity statistics.
6. Applying FDR correction.
7. Summarizing node strength for PCA_R.
8. Exploring the ACA_R-PCA_R connection across frequency bands.
9. Merging connectivity measures with behavioral sociability results for brain-behavior analyses.

The main connectivity comparison is across:
- genotype: `3xTg` vs `Ntg`
- sex: male vs female
- frequency band

Special attention is given to DMN-related connectivity:

```text
ACA_R-PCA_R
```

---

## Epoch folders

### `frame based epochs d2/`

This folder should contain the Day 2 epochs generated from behavioral frame information (videos).

These epochs represent periods in which the mouse was investigating:

- the cup with the mouse
- the empty cup

### `filtered epochs d2/`

This folder should contain cleaned Day 2 EEG epochs after filtering and artifact inspection.

Keep this folder separate from the frame-based epoch folder so that raw/intermediate and cleaned data are not overwritten.

---

## Suggested workflow

1. Run the behavioral analysis notebook:
   ```text
   Behavioral analysis/behavioral_analysis_day2.ipynb
   ```

2. Generate Day 2 behavioral results, including:
   - time spent with the mouse cup
   - time spent with the empty cup
   - total investigation time
   - sociability/discrimination index

3. Use behavioral interaction periods to create Day 2 EEG epochs.

4. Save frame-based epochs in:
   ```text
   frame based epochs d2/
   ```

5. Preprocess and visually inspect EEG epochs.

6. Save cleaned epochs in:
   ```text
   filtered epochs d2/
   ```

7. Run PSD analysis:
   ```text
   EEG analysis/psd_analysis_day2.ipynb
   ```

8. Run connectivity analysis:
   ```text
   EEG analysis/con_analysis_day2.ipynb
   ```

9. Compare behavioral and EEG measures across:
   - genotype
   - sex
   - interaction condition
   - frequency band

---

## Notes

- Day 2 is used for **sociability analysis**.
- Do not mix Day 2 and Day 3 epochs or behavioral output files.
- Keep raw EthoVision output, frame-based epochs, and filtered EEG epochs in separate folders.

---
## Expected outputs

The analysis can produce:

- sociability/discrimination index tables
- behavioral summary plots
- PSD plots by condition, genotype, sex, channel, and frequency band
- PSD ratio results
- connectivity matrices or channel-pair summaries
- connectivity statistics
- brain-behavior correlations

---
## Troubleshooting

### Notebook cannot find files

Check that the notebook is being run from the correct working directory and that file paths match the local folder structure.

### Subject IDs do not match

Make sure behavioral and EEG files use the same subject ID format before merging datasets.

### Missing epochs

Check whether the mouse investigated both cups. If a subject has no valid social or non-social epochs, it may need to be excluded from EEG comparisons.

### MNE or mne-connectivity import error

Install or update the required packages:

```bash
pip install --upgrade mne mne-connectivity
```

---
