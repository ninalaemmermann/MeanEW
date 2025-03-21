import numpy as np
import sys
sys.path.append('D:/Git/SimulationData_inPython/')
import dyca
import dyca_internal
from collections import Counter
import edfio
import math
import mne
from get_dict_with_seizure_information import get_sz_start_end
import matplotlib.pyplot as plt



def read_edf_file(edf_file_path, start: int = None, end: int = None):
    """
    Read an EDF file and return the data as a numpy array
    :param edf_file_path: path to the EDF file
    :return: call a function to return numpy array 
    """
    edf_file_object = edfio.read_edf(edf_file_path)
    sample_rate = get_SampleRate(edf_file_path)
    return get_array_from_edf(edf_file_object, sample_rate, start, end)

def get_array_from_edf(edf_data_object, sample_rate, start, end):
    """
    Get the data from an EDF file as a numpy array
    :param edf_data_object: EDF data object
    :param sample_rate: sampling rate of the EDF file
    :return: numpy array
    """
    edfsignals = edf_data_object.signals
    array = np.zeros((edf_data_object.num_signals, edfsignals[0].data.shape[0]))
    for i, j in zip(edfsignals, range(edf_data_object.num_signals)):  # some signals have another sampling rate
        if 'EEG' in i.label:
            normal_sampling_rate = i.sampling_frequency
        if i.data.shape[0] != array.shape[1] and 'EEG' not in i.label:
            ratio_sampling_rate = normal_sampling_rate / i.sampling_frequency
            array[j] = [item for item in i.data for _ in range(int(ratio_sampling_rate))]
        else:
            array[j] = i.data

    time_max = edf_data_object.duration
    time = np.linspace(0, time_max, array.shape[1])
    return time, array

def get_SampleRate(edf_file_path):
    raw = mne.io.read_raw_edf(edf_file_path, preload=True)
    return raw.info['sfreq']


def process_file(signal, window_duration, sample_rate, patient):
    """
    Process the signal in windows of a certain duration
    :param signal: signal to process
    :param window_duration: duration of the window in seconds
    :param sample_rate: sampling rate of the signal
    :offset: offset for the time points - for better understanding where in the signal the window is
    :return: time_points, first_eigenvalues, second_eigenvalues, third_eigenvalues"""

    # Total duration of the signal
    total_duration = signal.shape[1] / sample_rate

    # Calculate number of windows
    num_windows = int(np.floor(total_duration / window_duration))

    # Arrays to store eigenvalues for each window
    time_points = []
    first_eigenvalues = []
    second_eigenvalues = []
    third_eigenvalues = []

    # Calculate each window
    for i in range(num_windows):
        start_time = i * window_duration
        end_time = start_time + window_duration

        # Extract window segment
        start_segment = int(start_time * sample_rate)
        end_segment = int(end_time * sample_rate)
        signal_window = signal[:, start_segment:end_segment]

        if i == 4:
            print(signal_window)

        time_gesamt = np.linspace(0, total_duration, signal.shape[1])
        time = time_gesamt[start_segment:end_segment]
        #time_with_offset = start_time + offset

        # stoppe das aktuelle Fenster, wenn ersten 100 Eiträge in signal_window die gleichen sind. Die for schleife wird dann fortgesetzt
        #if np.sum(signal_window[:, 0] != signal_window[:, 80]) <= 10:
        if len(Counter(abs(signal_window[1][:30]))) <= 10:
            continue

        # Calculate Eigenvalues from DyCA
        eigenvalues = dyca.dyca(signal_window.transpose(), time_index=time, n=3, m=2)['generalized_eigenvalues']

        # Store results in lists
        time_points.append(start_time)
        first_eigenvalues.append({'patient': patient, 'eigenvalue': eigenvalues[0]})
        second_eigenvalues.append({'patient': patient, 'eigenvalue': eigenvalues[1]})
        third_eigenvalues.append({'patient': patient, 'eigenvalue': eigenvalues[2]})

    return time_points, first_eigenvalues, second_eigenvalues, third_eigenvalues


ABSZ_dict = get_sz_start_end(r"D:/Git/MeanEW/All_eigenvalues/GNSZ_seizures.csv")	

filtered_first_eigenvalues = []
filtered_second_eigenvalues = []
filtered_third_eigenvalues = []
bckg_first_eigenvalues = []
bckg_second_eigenvalues = []
bckg_third_eigenvalues = []


for i in range(len(ABSZ_dict)):
    patient = list(ABSZ_dict.keys())[i]
    sz_start_end = list(ABSZ_dict.values())[i]
    for j in range(len(sz_start_end)):
        start = math.ceil(sz_start_end[j][0])
        end = int(sz_start_end[j][1])
        file_path = f"D:\Git\MeanEW\All_eigenvalues\Data\GNSZ_seizure_WB\{patient}_res.OWN11101_filtWB_avg.edf"
        time, signal = read_edf_file(file_path)
        time_points, first_eigenvalues, second_eigenvalues, third_eigenvalues = process_file(signal, 3,256, patient)
        for k, time_point in enumerate(time_points):
            if start <= time_point < end:
                filtered_first_eigenvalues.append(first_eigenvalues[k])
                filtered_second_eigenvalues.append(second_eigenvalues[k])
                filtered_third_eigenvalues.append(third_eigenvalues[k])
            else:
                bckg_first_eigenvalues.append(first_eigenvalues[k])
                bckg_second_eigenvalues.append(second_eigenvalues[k])
                bckg_third_eigenvalues.append(third_eigenvalues[k])



# Calculate mean eigenvalues per patient
mean_first_eigenvalues = {}
mean_second_eigenvalues = {}
mean_third_eigenvalues = {}

bckg_mean_first_eigenvalues = {}
bckg_mean_second_eigenvalues = {}
bckg_mean_third_eigenvalues = {}

def calculate_mean_eigenvalues(eigenvalues_list):
    """
    Calculate the mean eigenvalues for each patient
    :param eigenvalues_list: list of eigenvalues dictionaries
    :return: dictionary of mean eigenvalues per patient
    """
    mean_first_eigenvalues = {}
    mean_second_eigenvalues = {}
    mean_third_eigenvalues = {}
    std_first_eigenvalues = {}
    std_second_eigenvalues = {}
    std_third_eigenvalues = {}

    for eigenvalue in eigenvalues_list[0]:
        patient = eigenvalue['patient']
        if patient not in mean_first_eigenvalues:
            mean_first_eigenvalues[patient] = []
            mean_second_eigenvalues[patient] = []
            mean_third_eigenvalues[patient] = []
        mean_first_eigenvalues[patient].append(eigenvalue['eigenvalue'])

    for eigenvalue in eigenvalues_list[1]:
        patient = eigenvalue['patient']
        mean_second_eigenvalues[patient].append(eigenvalue['eigenvalue'])

    for eigenvalue in eigenvalues_list[2]:
        patient = eigenvalue['patient']
        mean_third_eigenvalues[patient].append(eigenvalue['eigenvalue'])

    # Calculate the mean and standard deviation for each patient
    mean_first_eigenvalues = {patient: np.mean(values) for patient, values in mean_first_eigenvalues.items()}
    mean_second_eigenvalues = {patient: np.mean(values) for patient, values in mean_second_eigenvalues.items()}
    mean_third_eigenvalues = {patient: np.mean(values) for patient, values in mean_third_eigenvalues.items()}
    std_first_eigenvalues = {patient: np.std(values) for patient, values in mean_first_eigenvalues.items()}
    std_second_eigenvalues = {patient: np.std(values) for patient, values in mean_second_eigenvalues.items()}
    std_third_eigenvalues = {patient: np.std(values) for patient, values in mean_third_eigenvalues.items()}

    return mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues, std_first_eigenvalues, std_second_eigenvalues, std_third_eigenvalues

# Calculate mean and standard deviation eigenvalues for seizures
mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues, std_first_eigenvalues, std_second_eigenvalues, std_third_eigenvalues = calculate_mean_eigenvalues(
    [filtered_first_eigenvalues, filtered_second_eigenvalues, filtered_third_eigenvalues])

# Calculate mean and standard deviation eigenvalues for background
bckg_mean_first_eigenvalues, bckg_mean_second_eigenvalues, bckg_mean_third_eigenvalues, bckg_std_first_eigenvalues, bckg_std_second_eigenvalues, bckg_std_third_eigenvalues = calculate_mean_eigenvalues(
    [bckg_first_eigenvalues, bckg_second_eigenvalues, bckg_third_eigenvalues])



def plot_mean_eigenvalues(mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues, title):
    """
    Plot the mean eigenvalues for seizures or background
    :param mean_first_eigenvalues: dictionary of mean first eigenvalues
    :param mean_second_eigenvalues: dictionary of mean second eigenvalues
    :param mean_third_eigenvalues: dictionary of mean third eigenvalues
    :param title: title of the plot
    """
    # Plot the mean eigenvalues
    patients = list(mean_first_eigenvalues.keys())
    x = np.arange(len(patients))

    fig, ax = plt.subplots(figsize=(12, 8))

    bar_width = 0.25
    ax.bar(x - bar_width, mean_first_eigenvalues.values(), bar_width, label='First Eigenvalue')
    ax.bar(x, mean_second_eigenvalues.values(), bar_width, label='Second Eigenvalue')
    ax.bar(x + bar_width, mean_third_eigenvalues.values(), bar_width, label='Third Eigenvalue')

    ax.set_xlabel('Patients')
    ax.set_ylabel('Mean Eigenvalue')
    ax.set_title(title)
    ax.set_ylim(0, 1)
    ax.legend()

    plt.show()

    # Plot the distribution of eigenvalues
    fig, axs = plt.subplots(3, 1, figsize=(12, 18))

    # Round eigenvalues to one decimal place
    rounded_first_eigenvalues = [round(val, 2) for val in mean_first_eigenvalues.values()]
    rounded_second_eigenvalues = [round(val, 2) for val in mean_second_eigenvalues.values()]
    rounded_third_eigenvalues = [round(val, 2) for val in mean_third_eigenvalues.values()]

    # Plot histogram for first eigenvalues
    axs[0].hist(rounded_first_eigenvalues, bins=np.arange(0, 1.1, 0.1), edgecolor='black')
    axs[0].set_title('Histogram der einzelnen Eigenwerte (erster Eigenwert)')
    axs[0].set_xlabel('Eigenwert')
    axs[0].set_ylabel('Häufigkeit')

    # Plot histogram for second eigenvalues
    axs[1].hist(rounded_second_eigenvalues, bins=np.arange(0, 1.1, 0.1), edgecolor='black')
    axs[1].set_title('Histogram der einzelnen Eigenwerte (zweiter Eigenwert)')
    axs[1].set_xlabel('Eigenwert')
    axs[1].set_ylabel('Häufigkeit')

    # Plot histogram for third eigenvalues
    axs[2].hist(rounded_third_eigenvalues, bins=np.arange(0, 1.1, 0.1), edgecolor='black')
    axs[2].set_title('Histogram der einzelnen Eigenwerte (dritter Eigenwert)')
    axs[2].set_xlabel('Eigenwert')
    axs[2].set_ylabel('Häufigkeit')

    plt.tight_layout()
    plt.show()

def plot_metric(mean_first_eigenvalues, mean_second_eigenvalues, std_first_eigenvalues, std_second_eigenvalues, title):
    """
    Plot the metric (eigenvalue1 - eigenvalue2) / eigenvalue1 for each patient
    :param mean_first_eigenvalues: dictionary of mean first eigenvalues
    :param mean_second_eigenvalues: dictionary of mean second eigenvalues
    :param std_first_eigenvalues: dictionary of standard deviation of first eigenvalues
    :param std_second_eigenvalues: dictionary of standard deviation of second eigenvalues
    :param title: title of the plot
    """
    # Calculate the metric for each patient
    metric = {patient: (mean_first_eigenvalues[patient] - mean_second_eigenvalues[patient]) / mean_first_eigenvalues[patient] for patient in mean_first_eigenvalues.keys()}
    metric_std = {patient: np.sqrt((std_first_eigenvalues[patient]**2 + std_second_eigenvalues[patient]**2) / mean_first_eigenvalues[patient]**2) for patient in mean_first_eigenvalues.keys()}

    # Plot the metric
    patients = list(metric.keys())
    x = np.arange(len(patients))

    fig, ax = plt.subplots(figsize=(12, 8))

    ax.bar(x, metric.values(), yerr=metric_std.values(), capsize=5, label='(Eigenvalue1 - Eigenvalue2) / Eigenvalue1')

    ax.set_xlabel('Files')
    ax.set_ylabel('Metric')
    ax.set_title(title)
    ax.set_ylim(0, 1)
    ax.legend()

    plt.show()



# Call the function to plot the mean eigenvalues and standard deviation for seizures
plot_mean_eigenvalues(mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues, 'Mean Eigenvalues per File (Seizure)')

# Call the function to plot the mean eigenvalues and standard deviation for background
plot_mean_eigenvalues(bckg_mean_first_eigenvalues, bckg_mean_second_eigenvalues, bckg_mean_third_eigenvalues, 'Mean Eigenvalues per File (Non-Seizure)')


## Call the function to plot the metric for seizures
#plot_metric(mean_first_eigenvalues, mean_second_eigenvalues, std_first_eigenvalues, std_second_eigenvalues, 'Metric per File (Seizure)')

## Call the function to plot the metric for background
#plot_metric(bckg_mean_first_eigenvalues, bckg_mean_second_eigenvalues, bckg_std_first_eigenvalues, bckg_std_second_eigenvalues, 'Metric per File (Non-Seizure)')

# Calculate the standard deviation of the mean eigenvalues for seizures
std_mean_first_eigenvalues = np.std(list(mean_first_eigenvalues.values()))
std_mean_second_eigenvalues = np.std(list(mean_second_eigenvalues.values()))
std_mean_third_eigenvalues = np.std(list(mean_third_eigenvalues.values()))

# Calculate the standard deviation of the mean eigenvalues for background
bckg_std_mean_first_eigenvalues = np.std(list(bckg_mean_first_eigenvalues.values()))
bckg_std_mean_second_eigenvalues = np.std(list(bckg_mean_second_eigenvalues.values()))
bckg_std_mean_third_eigenvalues = np.std(list(bckg_mean_third_eigenvalues.values()))

# Plot the standard deviation of the mean eigenvalues
def plot_std_mean_eigenvalues(std_mean_first_eigenvalues, std_mean_second_eigenvalues, std_mean_third_eigenvalues, bckg_std_mean_first_eigenvalues, bckg_std_mean_second_eigenvalues, bckg_std_mean_third_eigenvalues, title):
    """
    Plot the standard deviation of the mean eigenvalues for seizures and background
    :param std_mean_first_eigenvalues: standard deviation of the mean first eigenvalues for seizures
    :param std_mean_second_eigenvalues: standard deviation of the mean second eigenvalues for seizures
    :param std_mean_third_eigenvalues: standard deviation of the mean third eigenvalues for seizures
    :param bckg_std_mean_first_eigenvalues: standard deviation of the mean first eigenvalues for background
    :param bckg_std_mean_second_eigenvalues: standard deviation of the mean second eigenvalues for background
    :param bckg_std_mean_third_eigenvalues: standard deviation of the mean third eigenvalues for background
    :param title: title of the plot
    """
    labels = ['First Eigenvalue', 'Second Eigenvalue', 'Third Eigenvalue']
    seizure_means = [np.mean(list(mean_first_eigenvalues.values())), np.mean(list(mean_second_eigenvalues.values())), np.mean(list(mean_third_eigenvalues.values()))]
    seizure_stds = [std_mean_first_eigenvalues, std_mean_second_eigenvalues, std_mean_third_eigenvalues]
    background_means = [np.mean(list(bckg_mean_first_eigenvalues.values())), np.mean(list(bckg_mean_second_eigenvalues.values())), np.mean(list(bckg_mean_third_eigenvalues.values()))]
    background_stds = [bckg_std_mean_first_eigenvalues, bckg_std_mean_second_eigenvalues, bckg_std_mean_third_eigenvalues]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.errorbar(x - width/2, seizure_means, yerr=seizure_stds, fmt='o', label='Seizure', capsize=5, color='blue')
    ax.errorbar(x + width/2, background_means, yerr=background_stds, fmt='o', label='Background', capsize=5, color='orange')

    ax.set_xlabel('Eigenvalues')
    ax.set_ylabel('Mean Eigenvalue with Standard Deviation')
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    plt.show()

# Call the function to plot the standard deviation of the mean eigenvalues
plot_std_mean_eigenvalues(std_mean_first_eigenvalues, std_mean_second_eigenvalues, std_mean_third_eigenvalues, bckg_std_mean_first_eigenvalues, bckg_std_mean_second_eigenvalues, bckg_std_mean_third_eigenvalues, 'Standard Deviation of Mean Eigenvalues')
