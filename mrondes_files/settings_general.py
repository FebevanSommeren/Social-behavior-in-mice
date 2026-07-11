"""
This file holds all general settings for the project, and can be imported and used in every script/notebook.
Each experiment has its own folder and accompanying settings file.
MIRTHE RONDE
"""
general = {
    "lab": "Kas_Lab",
    "experimenter": "Mirthe Ronde",
    "institution": "University of Groningen"
}

# dictionary holding the subject ids and their batch-cage combination identifiers
subject_id_batch_cage_dict = {
    'b1c1.1': 'b1c1.1_8989',
    'b1c1.2': 'b1c1.2_8993',
    'b1c1.3': 'b1c1.3_8982',
    'b1c1.4': 'b1c1.4_8995',
    'b1c2.1': 'b1c2.1_8990',
    'b1c2.2': 'b1c2.2_8903',
    'b1c2.3': 'b1c2.3_8998',
    'b1c2.4': 'b1c2.4_8981',
    'b1c3.1': 'b1c3.1_8987',
    'b1c3.2': 'b1c3.2_8996',
    'b1c3.3': 'b1c3.3_8994',
    'b1c3.4': 'b1c3.4_8983',
    'b1c4.1': 'b1c4.1_8992',
    'b1c4.2': 'b1c4.2_8985',
    'b1c4.3': 'b1c4.3_8997',
    'b1c4.4': 'b1c4.4_9000',
    'b2c1.1': 'b2c1.1_9001',
    'b2c1.2': 'b2c1.2_9007',
    'b2c1.3': 'b2c1.3_9002',
    'b2c1.4': 'b2c1.4_9005',
    'b2c2.1': 'b2c2.1_9012',
    'b2c2.2': 'b2c2.2_9010',
    'b2c2.3': 'b2c2.3_9020',
    'b2c2.4': 'b2c2.4_9003',
    'b2c3.1': 'b2c3.1_8988',
    'b2c3.2': 'b2c3.2_8991',
    'b2c3.3': 'b2c3.3_8986',
    'b2c3.4': 'b2c3.4_8999',
    'b2c4.1': 'b2c4.1_9013',
    'b2c4.2': 'b2c4.2_9017',
    'b2c4.3': 'b2c4.3_9019',
    'b2c4.4': 'b2c4.4_9006',
    'b3c1.1': 'b3c1.1_9009',
    'b3c1.2': 'b3c1.2_9008',
    'b3c1.3': 'b3c1.3_9004',
    'b3c1.4': 'b3c1.4_9018',
    'b3c2.1': 'b3c2.1_9014',
    'b3c2.2': 'b3c2.2_9016',
    'b3c2.3': 'b3c2.3_9011',
    'b3c3.1': 'b3c3.1_8858',
    'b3c3.2': 'b3c3.2_8760',
    'b3c3.3': 'b3c3.3_8851',
    'b3c3.4': 'b3c3.4_8859',
    'b3c4.1': 'b3c4.1_8857',
    'b3c4.2': 'b3c4.2_8854',
    'b3c4.3': 'b3c4.3_8855',
    'b3c4.4': 'b3c4.4_9015'
}

# EEG frequency bands used throughout the whole project for Power Spectral Density analysis
freq_bands_eeg = {
    r'$\delta$': (1, 4),  # Delta
    r'$\theta$': (4, 8),  # Theta
    r'$\alpha$': (8, 13),  # Alpha
    r'$\beta$': (13, 30),  # Beta
    r'$\gamma$': (30, 100)  # Gamma
}

# after inspecting the power traces of all subjects, these channels were noted as having bad quality
low_qual_chans = []

#######################################
## FILTERING / NWB CREATION SETTINGS ##
#######################################

# method of that will be used to filter the raw EEG signal; either 'mne' or 'scipy'
filter_method = 'mne'

# set to desired sampling frequency or to None if you do not wish to down-sample the EEG data
resample_freq = None

# variables used for raw EEG filtering while creating Neurodata Without Border (NWB) files (one of the first steps)
# BATCH 1 + 2
filtering_version_1 = {
    "lcut": 0.5,  # lower limit of desired band / filter (to be normalized)
    "hcut": 200,  # upper limit of desired band / filter (to be normalized)
    "art": 3,  # std of the signal is multiplied by this value to filter out additional artifacts
    "low_val": 0.006,  # lower value of artifact removal (caused by package loss)
    "high_val": 0.013,  # upper value of artifact removal (caused by package loss)
    "electrode_info": {
        "EEG 3": ["AI_L", 1.3, 2.5, 3.5, "depth"],
        "EEG 4": ["S1_L", -0.5, 3, 0, "skull"],
        "EEG 7": ["A1_L", -2, 3.8, 0, "skull"],
        "EEG 9": ["A1_R", -2, -3.8, 0, "skull"],
        "EEG 12": ["ACA_R", 1.3, -0.6, 2, "depth"],
        "EEG 10": ["AI_R", 1.3, -2.5, 3.5, "depth"],
        "EEG 11": ["PMC_R", 2.2, -1.7, 1.2, "depth"],
        "EEG 13": ["PCA_R", -0.9, -0.5, 1, "depth"],
        "EEG 6": ["EMG_L", 0, 0, 0, "emg"],
        "EEG 8": ["EMG_R", 0, 0, 0, "emg"]
    }
}

# NEWER TAINI VERSION
# variables used for raw EEG filtering while creating Neurodata Without Border (NWB) files (one of the first steps)
# BATCH 3
filtering_version_2 = {
    "lcut": 0.5,  # lower limit of desired band / filter (to be normalized)
    "hcut": 200,  # upper limit of desired band / filter (to be normalized)
    "art": 3,  # std of the signal is multiplied by this value to filter out additional artifacts
    "low_val": 0.006,  # lower value of artifact removal (caused by package loss)
    "high_val": 0.013,  # upper value of artifact removal (caused by package loss)
    "electrode_info": { ## MAKE SURE TO USE THE CORRECT NUMBERING, IT IS THE PIN NUMBER IN THE IMPLANT -1
        "EEG 4": ["AI_L", 1.3, 2.5, 3.5, "depth"],
        "EEG 5": ["S1_L", -0.5, 3, 0, "skull"],
        "EEG 8": ["A1_L", -2, 3.8, 0, "skull"],
        "EEG 10": ["A1_R", -2, -3.8, 0, "skull"],
        "EEG 13": ["ACA_R", 1.3, -0.6, 2, "depth"],
        "EEG 11": ["AI_R", 1.3, -2.5, 3.5, "depth"],
        "EEG 12": ["PMC_R", 2.2, -1.7, 1.2, "depth"],
        "EEG 14": ["PCA_R", -0.9, -0.5, 1, "depth"],
        "EEG 7": ["EMG_L", 0, 0, 0, "emg"],
        "EEG 9": ["EMG_R", 0, 0, 0, "emg"]
    }
}

channel_name_dict = {
    'AI_L': 'Left Anterior Insula (depth)',
    'S1_L': 'Left Sensory S1 Cortex (skull)',
    'A1_L': 'Left Auditory A1 Cortex (skull)',
    'A1_R': 'Right Auditory A1 Cortex (skull)',
    'ACA_R': 'Right Anterior Cingulate Cortex (depth)',
    'AI_R': 'Right Anterior Insula (depth)',
    'PMC_R': 'Right Premotor Cortex (depth)',
    'PCA_R': 'Right Posterior Cingulate Cortex (depth)'
}

###################################
## FRAME BASED EPOCHING SETTINGS ##
###################################

# is your filtered EEG in your NWB also resampled?
resampled = False

# if your filtered EEG in the NWB files is not resampled, then set the package loss cutoff
package_loss_cutoff = 0.15  # max percentage of package loss that is allowed (as a fraction)

# minimum duration of the interaction between mouse and cup/mouse (in seconds)
# set to None if you do not wish to require a minimum event duration
min_event_duration = None

# the desired epoch length the events will be divided into
desired_epoch_length = 1.0

# whether to overlap epochs at all
overlap_epochs = False

# the maximum percentage (as a fraction) of information duplication between epochs we allow
# this would mean that with a cutoff of 50% (epoch_overlap_cutoff=0.5), an interaction of duration 1.4 would yield one
# epoch of 1 second (60.0% duplication), i.e. the 0.4 seconds of data is deleted.

# CHANGED EXAMPLE
# Example:
# If desired_epoch_length = 1 second and an event lasts 1.4 seconds,
# covering the full event would require ~0.6 seconds overlap (60%).
#
# If epoch_overlap_cutoff = 0.5, the required overlap (0.6) exceeds the allowed maximum (0.5),
# so overlap is set to 0 and only one epoch is created (last 0.4 seconds is discarded).
epoch_overlap_cutoff = 0.5

####################
## OTHER SETTINGS ##
####################


# ADDED
sex_dict = { 
    "b1c1.1": "m", "b1c1.2": "m", "b1c1.3": "m", "b1c1.4": "m",
    "b1c2.1": "m", "b1c2.2": "m", "b1c2.3": "m", "b1c2.4": "m",
    "b1c3.1": "f", "b1c3.2": "f", "b1c3.3": "f", "b1c3.4": "f",
    "b1c4.1": "f", "b1c4.2": "f", "b1c4.3": "f", "b1c4.4": "f",
    "b2c1.1": "m", "b2c1.2": "m", "b2c1.3": "m", "b2c1.4": "m",
    "b2c2.1": "m", "b2c2.2": "m", "b2c2.3": "m", "b2c2.4": "m",
    "b2c3.1": "f", "b2c3.2": "f", "b2c3.3": "f", "b2c3.4": "f",
    "b2c4.1": "f", "b2c4.2": "f", "b2c4.3": "f", "b2c4.4": "f",
    "b3c1.1": "m", "b3c1.2": "m", "b3c1.3": "m", "b3c1.4": "m", 
    "b3c2.1": "m", "b3c2.2": "m", "b3c2.3": "m", "b3c2.4": "m",
    "b3c3.1": "f", "b3c3.2": "f", "b3c3.3": "f", "b3c3.4": "f",
    "b3c4.1": "f", "b3c4.2": "f", "b3c4.3": "f", "b3c4.4": "f",
}

