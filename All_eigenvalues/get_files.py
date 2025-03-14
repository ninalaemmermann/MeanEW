# get files from GPU server
import os
import paramiko
import stat
import pandas as pd
import numpy as np

# get files from excel file and store in dataframe
def get_files_from_csv(csv_file_path):
    df = pd.read_csv(csv_file_path, encoding = 'utf-8', sep=";", usecols = ['Column1','Gender  ', 'Age     ', 'Duration', 'BName', 'Sz start', 'Sz stop', 'Spalte1', 'ARTF', 'BCKG', 'SEIZ', 'UNKNOWN', 'FNSZ', 'GNSZ', 'FNSZ1st', 'GNSZ1st', 'SPSZ', 'CPSZ', 'ABSZ', 'TNSZ', 'CNSZ', 'TCSZ', 'ATSZ', 'MYSZ', 'NESZ'])
    return df
    
data_seizures = get_files_from_csv(r"D:/Git/MeanEW/All_eigenvalues/ABSZ_seizures.csv")

# get a list of the filenames as stored
file_name = []
for i in data_seizures["BName"]:
    i = f"{i}" + "_res.OWN11101_filtWB_avg.edf"
    file_name.append(i)



# download files from GPU server with ssh
def download_files_from_server(server_name, username, password, localpath, remotepath, file_list):
        """
        Download files from server
        :param server_name: name of the server
        :param username: username for the server
        :param password: password for the server
        :param localpath: local path where the files should be stored
        :param remotepath: remote path where the files are stored
        :param file_list: list of the files to be downloaded
        """
        if file_list is None or len(file_list) == 0:
            print("No files to download")
            return
        
        # Stelle sicher, dass der lokale Pfad existiert
        os.makedirs(localpath, exist_ok=True)

        # Verbindung zum Server herstellen
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server_name, username=username, password=password)
        print("Connected to server")
        ftp = ssh.open_sftp()

        try:
            server_files = ftp.listdir(remotepath)
            print(f"Found {len(server_files)} files at {remotepath}")

            # Zähler für heruntergeladene Dateien
            downloaded_files = 0

            # Dateien herunterladen, die in der Liste enthalten sind
            for filenames in server_files:
                if filenames in file_list:
                    remote_file_path = f"{remotepath}/{filenames}"
                    local_file_path = os.path.join(localpath, filenames)

                    print(f"Downloading {remote_file_path} to {local_file_path}")

                    ftp.get(remote_file_path, local_file_path)
                    downloaded_files += 1
            
            print(f"Download complete. Downloaded {downloaded_files} files of {len(file_list)}")

            # Dateien, die nicht gefunden wurden
            not_found_files =  [f for f in file_list if f not in server_files]
            if not_found_files:
                print(f"Files not found: {not_found_files}")

        except Exception as e:
            print(f"Error while downloading files: {e}")

        finally:
            if 'ftp' in locals():
                ftp.close()
            if 'ssh' in locals():
                ssh.close()
            print("Disconnected from server")



        # def search_files(remotepath):
        #     found_files = []

        #     try:
        #         items = ftp.listdir_attr(remotepath)

        #         for item in items:
        #              full_path = os.path.join(remotepath, item.filename)
                    
        #              if stat.S_ISDIR(item.st_mode): # ist ein Ordner
        #                 # Rekursiv in Unterordner gehen
        #                 found_files.extend(search_files(full_path))
                    
        #              else: # ist eine Datei
        #                  # Prüfe, ob Dateiname in der Liste enthalten ist
        #                  if item.filename in file_list:
        #                      found_files.append(full_path)
        #                      print(f"Found file {item.filename}")
        #     except Exception as e:
        #         print(f"Error while searching from {remotepath}: {e}")
            
        #     return found_files
    

if __name__ == "__main__":
    # Configurations
    SERVER_NAME = "141.39.193.192"
    USERNAME = "ninalaemmermann"
    PASSWORD = "sonnige%Aussichten5"

    # Server paths
    REMOTE_PATH = "/home/data/deepeeg/temple_uni/v2.0.3/besa_preprocessed_by_annika/artifact_correction_no_bad/WB/avg/train"
    LOCAL_PATH = "D:\\Git\\MeanEW\\All_eigenvalues\\Data\\ABSZ_seizure_WB"

    # Liste der Dateien, die heruntergeladen werden sollen
    FILES_TO_DOWNLOAD = file_name

    # Starte den Download
    download_files_from_server(
        server_name=SERVER_NAME,
        username=USERNAME,
        password=PASSWORD, 
        remotepath=REMOTE_PATH,
        localpath=LOCAL_PATH,
        file_list=FILES_TO_DOWNLOAD
    )