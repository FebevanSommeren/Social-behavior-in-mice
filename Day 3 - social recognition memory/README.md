# Day 3 - Social Recognition Memory

This folder contains the analysis pipeline for **Day 3 of the three-chamber social interaction paradigm**, which tests **social recognition memory** in pre-pathological 3xTg-AD mice and non-transgenic control mice.

On Day 3, each mouse explores a three-chamber arena containing:

- one cup with a novel mouse: the **novel stimulus**
- one cup with the mouse from day 2: the **familiar stimulus**

The main goal is to quantify how much time the test mouse spends investigating the novel stimulus compared with the familiar cup, and to analyze EEG activity during those same behaviorally defined interaction periods.

---

## Folder structure

```text
Day 3 - social recognition memory/
├── __init__.py
├── README.md
├── Behavioral analysis/
│   └── behavioral_analysis_day3.ipynb
├── EEG analysis/
│   ├── psd_analysis_day3.ipynb
│   └── con_analysis_day3.ipynb
├── filtered epochs d3/
└── frame based epochs d3/
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

The behavioral analysis uses EthoVision output files from Day 3 to calculate social novelty-related measures.

The main notebook is:

```text
behavioral_analysis_day3.ipynb
```

This notebook:

1. Loads and processes Day 3 EthoVision Excel files.
2. Extracts time spent investigating the novel cup and the familiar cup.
3. Calculates total investigation time.
4. Calculates the discrimination index.
5. Visualizes social novelty measures by genotype and sex.
6. Performs statistical analyses, including assumption checks and two-way ANOVAs.

### Discrimination index

Social recognition memory is quantified using a social novelty index:

$
SNI = \frac{t_{novel} - t_{familiar}}{t_{novel} + t_{familiar}}
$

where:

- `t_novel` = time spent investigating the cup containing the novel mouse
- `t_familiar` = time spent investigating the familiar mouse cup

The index ranges from `-1` to `1`:

- `1` = exclusive preference for the novel stimulus
- `0` = no preference 
- `-1` = exclusive preference for the familiar stimulus

---

## EEG analysis

The EEG analysis uses Day 3 epochs that were created from behaviorally relevant interaction periods.

For Day 3, the relevant EEG conditions are:

- **novel cup**: epochs when the test mouse investigates the novel stimulus
- **familiar cup**: epochs when the test mouse investigates the familiar stimulus

The EEG analysis consists of two main parts:

1. **Power spectral density (PSD) analysis**
2. **Connectivity analysis**

---

## PSD analysis

The main notebook is:

```text
psd_analysis_day3.ipynb
```

This notebook analyzes spectral power during Day 3 epochs.

It includes:

1. Loading subject-level Day 3 epochs.
2. Checking the number of subjects and epoch distribution.
3. Calculating subject-wise PSD summaries.
4. Checking for outliers and visually inspecting flagged subjects.
5. Plotting normalized PSDs across subjects, genotype, sex, and interaction type.
6. Calculating the PSD ratio between novel and familiar interaction epochs.
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
con_analysis_day3.ipynb
```

This notebook analyzes functional connectivity during Day 3 epochs.

The main connectivity measures are:

- `wpli2_debiased`: debiased squared weighted phase-lag index
- `dpli`: directed phase-lag index

The notebook includes:

1. Loading subject-level Day 3 epochs.
2. Defining relevant EEG channels.
3. Calculating connectivity for novel and familiar interaction epochs.
4. Plotting genotype and sex differences in connectivity.
5. Calculating channel-pair connectivity statistics.
6. Applying FDR correction.
7. Summarizing node strength for PCA_R.
8. Exploring the ACA_R-PCA_R connection across frequency bands.
9. Merging connectivity measures with behavioral results for brain-behavior analyses.

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

### `frame based epochs d3/`

This folder should contain the Day 3 epochs generated from behavioral frame information (videos).

These epochs represent periods in which the mouse was investigating:

- the novel cup 
- the familiar cup

### `filtered epochs d3/`

This folder should contain cleaned Day 3 EEG epochs after filtering and artifact inspection.

Keep this folder separate from the frame-based epoch folder so that raw/intermediate and cleaned data are not overwritten.

---

## Suggested workflow

1. Run the behavioral analysis notebook:
   ```text
   Behavioral analysis/behavioral_analysis_day3.ipynb
   ```

2. Generate Day 3 behavioral results, including:
   - time spent with the novel cup
   - time spent with the familiar cup
   - total investigation time
   - discrimination index

3. Use behavioral interaction periods to create Day 3 EEG epochs.

4. Save frame-based epochs in:
   ```text
   frame based epochs d3/
   ```

5. Preprocess and visually inspect EEG epochs.

6. Save cleaned epochs in:
   ```text
   filtered epochs d3/
   ```

7. Run PSD analysis:
   ```text
   EEG analysis/psd_analysis_day3.ipynb
   ```

8. Run connectivity analysis:
   ```text
   EEG analysis/con_analysis_day3.ipynb
   ```

9. Compare behavioral and EEG measures across:
   - genotype
   - sex
   - interaction condition
   - frequency band

---

## Notes

- Day 3 is used for **social recognition memory**.
- Do not mix Day 2 and Day 3 epochs or behavioral output files.
- Keep raw EthoVision output, frame-based epochs, and filtered EEG epochs in separate folders.

---
## Expected outputs

The analysis can produce:

- Discrimination index tables
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

Check whether the mouse investigated both cups. If a subject has no valid novel or familiar cup epochs, it may need to be excluded from EEG comparisons.

### MNE or mne-connectivity import error

Install or update the required packages:

```bash
pip install --upgrade mne mne-connectivity
```

---