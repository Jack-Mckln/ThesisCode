import numpy as np 
import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import socket 
import re
import os
import h5py
import scipy.signal as sc
import seaborn as sns

### Determining which computer I am on to set the correct paths (not having to edit paths each time I change computer) ###

hostname = socket.gethostname()

if hostname == 'LAPTOP-KD3QCCE5':
    user_path = Path(r'C:\Users\jackm')
    
else:
    user_path = Path(r'C:\Users\jpm93')

### Function to open and read the correct data ###
def read_nxs(filename): 
    '''
    This will return a tuple in the form: (q_values, data).
    
    The data will have a shape dependent on if multiple SAXS patterns are stored 
    in the .nxs file. 
    
    For example, data from different positions along a capillary will be in the 
    form [x,y,z]:
        x = frame number (multiple frames if .nxs is a scan across a capillary/droplet etc.)
        y = intensity 
        z = q axis with a length of the number of q values 
    
    if I want to access the first frame of a scan, I would type:
        data[0,:,:]
        i.e. all of the intensities (y) at every q (z) for the first (0th) frame 
    
    check the shape of your data by using data.shape
    
    If it's just a single SAXS image, "data" will just be the intensity value at each q value
    
    '''
    
    with h5py.File(filename,'r') as hdf:
       data_arr = np.array(hdf.get('entry/data1d/I'))
       q = np.array(hdf.get('entry/data1d/q'))

    return data_arr, q

### FUNCTION TO CREATE LISTS WITH THE REELVANT SAXS/WAXS FILES  ###
def glob_re(pattern, strings):
    return list(filter(re.compile(pattern).match, strings)) #This isn't the best way to do this as it doesn't take advantage of lazy evaluation but it works and I dont really understand laziness yet

def data_collection(file_list, type):
    intensities = []
    for file in file_list:
        data = pd.read_csv(folder_path / file, skiprows=2, 
                           sep=' ', names = ['q', 'I', 'error'])
        I = np.array(data['I'])

        if type == 'SAXS':
            I[52] = None  #these are hot pixels in SAXS
            I[185] = None
        

        intensities.append(I)

    return data['q'], intensities

#function to sort the highest numebrs from a list and retain their indices
def sep_low_high_N_elements_with_indices(numbers, N): # N is the nubmer of lowest elements
    # Create a list of tuples (index, value)
    indexed_numbers = list(enumerate(numbers))  # [(0, 10), (1, 20), (2, 11), ...]

    # Sort the list of tuples by the value (second element) in descending order
    indexed_numbers.sort(key=lambda pair: pair[1])

    # Extract the top x elements and their indices
    bottom_N_elements_with_indices = indexed_numbers[:N]
    top_elements_ind = indexed_numbers[N:]

    # Separate the values and their indices
    #bottom values
    bottom_N_elements = [pair[1] for pair in bottom_N_elements_with_indices]
    bottom_indices = [pair[0] for pair in bottom_N_elements_with_indices]
    #top values
    top_N_elements = [pair[1] for pair in top_elements_ind]
    top_indices = [pair[0] for pair in top_elements_ind]

    return bottom_N_elements, bottom_indices, top_N_elements, top_indices
        

def build_bkg(path, file_list, N):
    data, q = read_nxs(path/file_list[0])
    data_integrated = np.sum(data, axis = 1)
    _, bot_ind, _,_ = sep_low_high_N_elements_with_indices(data_integrated, N)

    ##create a np array to be populated with all the N lowest values (the bacgkround)
    bkg_data = []
    for x in bot_ind:
        bkg_data.append(data[x])
    
    #convert it into a np array because nicer and easier
    bkg_data = np.array(bkg_data)
    bkg_data_ave = np.mean(bkg_data, axis = 0)
    #calculate the emans and standard deivation of the background data
    integrated_data = np.sum(bkg_data, axis = 1)
    avg_bkg = np.mean(integrated_data, axis = 0)
    std_bkg = np.std(integrated_data, axis = 0)

    return bkg_data_ave, avg_bkg, std_bkg

def compare_top(path,file_list,N):

    retained_arrs = [] # this will be populated by the arrays that pass the selection criteria
    for file in file_list:
        data,q = read_nxs(path/file)
        data_integrated = np.sum(data, axis = 1)
        _,_,_,top_ind = sep_low_high_N_elements_with_indices(data_integrated, N)

        bkg_data_ave, avg_bkg, std_bkg = build_bkg(path,file_list,N)   
        bkg_data_ave_int = np.sum(bkg_data_ave, axis = 0)

        int_vals = []
        retained = [] #temporary storage for the retained files
        for x in top_ind:
            intensities = data[x]
            integrated = np.sum(intensities, axis=0)
            #applying the elesction criteria
            if integrated - bkg_data_ave_int > 4*std_bkg:
                retained.append(data[x])

            ##if no files staisy the criteria, populate an array with blank values in the correct
            ##length to allow plotting to work correctly
            #elif retained == []:
            #    retained.append([None]*len(q))


            int_vals.append(integrated)

        int_vals = np.array(int_vals)
        diff_from_bkg = int_vals - bkg_data_ave_int

        # take the average of the retianed files so that we only have one file by the end that correspond to this frame
        #and append it to the list we are keeping
        retained_arrs.append(np.mean(retained, axis = 0))

    #if any files aren't working (giving nan) then delete them
    for i,x in enumerate(retained_arrs):
        try:
            if np.isnan(x).any():
                retained_arrs[i] = np.nan

        except TypeError:
                retained_arrs[i] = np.nan
    #Now that we've filtered them I delete the problematic ones (e.g. ones with None)
    retained_arrs = [arr for arr in retained_arrs if not np.isnan(arr).any()]

    return int_vals, diff_from_bkg, retained_arrs, q, bkg_data_ave

def plotting(path, N):

    _,_, retained_waxs, q_waxs, bkg_data_waxs = compare_top(path, WAXS_file_list, N)
    _,_, retained_saxs, q_saxs, bkg_data_saxs = compare_top(path, SAXS_file_list, N)

    retained_waxs_ave = np.mean(retained_waxs, axis = 0)
    retained_saxs_ave = np.mean(retained_saxs, axis = 0)

    fig_waxs, ax_waxs = plt.subplots()
    fig_saxs, ax_saxs = plt.subplots()
    
    ax_waxs.plot(q_waxs, retained_waxs_ave, label = 'average')
    ax_waxs.plot(q_waxs, retained_waxs_ave-bkg_data_waxs, label = 'background substracted')

    ax_saxs.plot(q_saxs, retained_saxs_ave, label = 'average')
    ax_saxs.plot(q_saxs, retained_saxs_ave-bkg_data_saxs, label = 'background substracted') 

    ax_waxs.set_yscale('log')
    ax_waxs.set_xlabel('q (nm$^{-1}$)')
    ax_waxs.set_ylabel('Intensity (Arb. Units)')
    ax_waxs.legend()

    ax_saxs.set_yscale('log')
    ax_saxs.set_xlabel('q (nm$^{-1}$)')
    ax_saxs.set_ylabel('Intensity (Arb. Units)')
    ax_saxs.legend()

    fig_waxs.savefig(folder_path/'waxs.png', dpi = 600, bbox_inches = 'tight')
    fig_saxs.savefig(folder_path/'saxs.png', dpi = 600, bbox_inches = 'tight')


process_path = user_path / r'OneDrive - University of Bath\PhD\Data\FDC\FDC Max IV\process\azint'
folder_path = process_path / r'chicken bag windows'
folder_path = folder_path / r'NaCl, 21RH, 23cm'

WAXS_file_list = glob_re(r'.*pilatus_integrated.h5', os.listdir(folder_path))
SAXS_file_list = glob_re(r'.*eiger_integrated.h5', os.listdir(folder_path)) 

plotting(folder_path, 20)

