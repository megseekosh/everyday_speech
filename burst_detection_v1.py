import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate as interpolate

def count_contiguous_segments(arr):
    not_nan_segments = np.where(~np.isnan(arr))[0]

    if not_nan_segments.size == 0:
        return 0

    # Find the indices where the segments change
    segment_changes = np.where(np.diff(not_nan_segments) > 1)[0]

    # Add 1 to account for the first segment
    return len(segment_changes) + 1

def lengths_of_non_nan_segments(arr):
    if not arr.size:  # Check if array is empty
        return np.array([])

    # Initialize variables
    lengths = []
    current_length = 0

    for value in arr:
        if not np.isnan(value):
            current_length += 1
        else:
            if current_length > 0:
                lengths.append(current_length)
                current_length = 0

    # Add the length of the last segment if it's non-NaN
    if current_length > 0:
        lengths.append(current_length)

    return np.array(lengths)
    
real_data = pd.read_csv('./dataframes/everyday_cds_ods.csv', index_col = 0)

i = 0

compiled_results = []

fig, axs = plt.subplots(figsize=(12,140), nrows=50, ncols=2) # update arguments for more children

for child in real_data['child_id'].unique():
    data = real_data.loc[real_data['child_id'] == child]
    data = data.reset_index()['AWC_COUNT']

    f = interpolate.interp1d(np.linspace(0,len(data), len(data)), data)

    xnew = np.arange(0, len(data), 0.1) # x-axis (# segments); interpolate 
    ynew = f(xnew) 

    baseline = np.median(ynew)
    std = np.std(ynew)

    bursts = np.full([len(ynew),1], np.nan)
    bursts = np.concatenate(bursts, axis=0) # the array with the counts


    for time in range(len(ynew)):
        if ynew[time] > 3*std: # pretty sure this is where he classifies bursts 
            bursts[time] = ynew[time]

    mean_burst_amplitude = np.mean(bursts[~np.isnan(bursts)])
    mean_burst_std = np.std(bursts[~np.isnan(bursts)])
    bursts_count = count_contiguous_segments(bursts)

    burst_lengths = lengths_of_non_nan_segments(bursts)
    mean_burst_length = np.mean(burst_lengths)
    std_burst_length = np.std(burst_lengths)
    
    if i < 100: # for only these child IDs
        axs[i//2, i%2].plot(np.linspace(0,len(ynew),len(ynew)), ynew, color='b', lw=4)
        axs[i//2, i%2].plot(np.linspace(0,len(ynew),len(ynew)), bursts, color='r', lw=4)

        axs[i//2, i%2].set_title(f'child_id = {child}')
        axs[i//2, i%2].grid()
    
    i += 1
    
    compiled_results.append([child, bursts_count, burst_lengths, mean_burst_length, std_burst_length, mean_burst_amplitude, mean_burst_std])

#     print (f'child_id = {child}')
#     print (f'burst_count = {bursts_count}\nburst_lengths = {burst_lengths}\nmean_burst_length = {mean_burst_length}\nstd_burst_length = {std_burst_length:.2f}')
#     print (f'mean_burst_amplitude = {mean_burst_amplitude:.2f}\nmean_burst_std = {mean_burst_std:.2f}\n')

compiled_results_df = pd.DataFrame.from_records(compiled_results, 
                        columns=['child_id', 'bursts_count', 'burst_lengths', 'mean_burst_length', 
                                 'std_burst_length', 'mean_burst_amplitude', 'mean_burst_std']) 

compiled_results_df.to_csv('./dataframes/burstiness_compiled_results.csv', sep=',', encoding='utf-8', index=False)

plt.tight_layout()
plt.savefig('burstiness_100_children.png', dpi=100)

#     i += 1
#     if i > 5:
#         break