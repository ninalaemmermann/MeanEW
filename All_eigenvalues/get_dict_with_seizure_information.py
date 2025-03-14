
import pandas as pd

# get sz start nad sz end per pateint from csv. One file/patient can contain more than one sz start and sz end
# Sz start and sz end should be tailed to its corresponding patient
# Store in a dictionary

def get_sz_start_end(file):
    '''
    Get sz start and sz end per patient from csv file
    file: csv file
    return: dictionary with patient as key and sz start and sz end as value
    '''
    df = pd.read_csv(file, encoding = 'utf-8', sep=";", usecols = ['BName','Sz start', 'Sz stop'])
    sz_start_end = {}
    for i in range(len(df)):
        patient = df['BName'][i]
        sz_start = df['Sz start'][i]
        sz_end = df['Sz stop'][i]
        if patient in sz_start_end:
            sz_start_end[patient].append((sz_start, sz_end))
        else:
            sz_start_end[patient] = [(sz_start, sz_end)]
    return sz_start_end

#ABSZ_dict = get_sz_start_end(r"D:/Git/All_eigenvalues/ABSZ_seizures.csv")


