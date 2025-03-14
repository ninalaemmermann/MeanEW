import numpy as np
import sys
sys.path.append('D:/Git/SimulationData_inPython/')
import dyca
import dyca_internal
from collections import Counter
import edfio
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


ABSZ_dict = get_sz_start_end(r"D:/Git/MeanEW/All_eigenvalues/ABSZ_seizures.csv")	

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
        start = int(sz_start_end[j][0])
        end = int(sz_start_end[j][1])
        file_path = f"D:\Git\MeanEW\All_eigenvalues\Data\ABSZ_seizure_WB\{patient}_res.OWN11101_filtWB_avg.edf"
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

    # Calculate the mean for each patient
    mean_first_eigenvalues = {patient: np.mean(values) for patient, values in mean_first_eigenvalues.items()}
    mean_second_eigenvalues = {patient: np.mean(values) for patient, values in mean_second_eigenvalues.items()}
    mean_third_eigenvalues = {patient: np.mean(values) for patient, values in mean_third_eigenvalues.items()}

    return mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues

# Calculate mean eigenvalues for seizures
mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues = calculate_mean_eigenvalues(
    [filtered_first_eigenvalues, filtered_second_eigenvalues, filtered_third_eigenvalues])

# Calculate mean eigenvalues for background
bckg_mean_first_eigenvalues, bckg_mean_second_eigenvalues, bckg_mean_third_eigenvalues = calculate_mean_eigenvalues(
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
    ax.set_xticks(x)
    ax.set_xticklabels(patients)
    ax.set_ylim(0, 1)
    ax.legend()

    plt.show()

# Call the function to plot the mean eigenvalues for seizures
plot_mean_eigenvalues(mean_first_eigenvalues, mean_second_eigenvalues, mean_third_eigenvalues, 'Mean Eigenvalues per Patient (Seizure)')

# Call the function to plot the mean eigenvalues for background
plot_mean_eigenvalues(bckg_mean_first_eigenvalues, bckg_mean_second_eigenvalues, bckg_mean_third_eigenvalues, 'Mean Eigenvalues per Patient (Background)')




