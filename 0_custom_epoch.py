import os
import pandas as pd
import re
from decimal import *

# custom_epoch
# input: its file
# looks at conversation and pause tagged lines
    # fills in the values for each field per each conversation/pause
    # each is a list of the same length, where each index represents a row in the future df
# each row is of varying time lengths, so split each row into 60 seconds
    # each row can CUT or COMBINE
        # CUT: time length > 60. take only 60 seconds and insert a new "row" right after with remaining time. process next row
        # COMBINE: time length < 60. add everything from the next row to current row
            # if time is greater than 60, CUT
            # if time is less than 60, COMBINE
            # if time == 60, process next row
        # process next row if time length == 60
# output: csv file that can be inputted into cds/sleep classifier

'''
HELPER FUNCTIONS
'''
def get_values(vals, line):
    # if ratio != 1, this means it's a portion of the full conversation

    # curr_AWC
    match_femAWC = re.search(r'femaleAdultWordCnt="([^"]+)"', line)
    if match_femAWC is not None:
        get_femAWC = float(match_femAWC.group(1))
        #print(str(get_femAWC))
        vals['curr_AWC'] = vals['curr_AWC'] + get_femAWC

    match_malAWC = re.search(r' maleAdultWordCnt="([^"]+)"', line) # make sure to have a space before
    if match_malAWC is not None:
        get_malAWC = float(match_malAWC.group(1))
        #print(str(get_malAWC))
        vals['curr_AWC'] = vals['curr_AWC'] + get_malAWC

    # curr_CT
    match_turnTake = re.search(r'turnTaking="([^"]+)"', line)
    if match_turnTake is not None:
        get_turnTake = int(match_turnTake.group(1))
        vals['curr_CT'] = vals['curr_CT'] + get_turnTake

    # curr_CV
    match_childUtt = re.search(r'childUttCnt="([^"]+)"', line)
    if match_childUtt is not None:
        get_match_childUtt = int(match_childUtt.group(1))
        vals['curr_CV'] = vals['curr_CV'] + get_match_childUtt

    # curr_Meaning
    match_MAN = re.search(r'MAN="([^"]+)"', line)
    if match_MAN is not None:
        get_match = float(match_MAN.group(1)[1:-1]) # ex. P4.57S
        vals['curr_Meaning'] = vals['curr_Meaning'] + get_match
    
    match_FAN = re.search(r'FAN="([^"]+)"', line)
    if match_FAN is not None:
        get_match = float(match_FAN.group(1)[1:-1])
        vals['curr_Meaning'] = vals['curr_Meaning'] + get_match # get_match = 5.67
    
    match_CHN = re.search(r'CHN="([^"]+)"', line)
    if match_CHN is not None:
        get_match = float(match_CHN.group(1)[1:-1])
        vals['curr_Meaning'] = vals['curr_Meaning'] + get_match

    match_CXN = re.search(r'CXN="([^"]+)"', line)
    if match_CXN is not None:
        get_match = float(match_CXN.group(1)[1:-1])
        vals['curr_Meaning'] = vals['curr_Meaning'] + get_match

    # curr_TV
    match_TVN = re.search(r'TVN="([^"]+)"', line)
    if match_TVN is not None:
        get_match_TVN = float(match_TVN.group(1)[1:-1])
        vals['curr_TV'] = vals['curr_TV'] + get_match_TVN

    # curr_Noise
    match_NON = re.search(r'NON="([^"]+)"', line)
    if match_NON is not None:
        get_match_NON = float(match_NON.group(1)[1:-1])
        vals['curr_Noise'] = vals['curr_Noise'] + get_match_NON

    # curr_Silence
    match_SIL = re.search(r'SIL="([^"]+)"', line)
    if match_SIL is not None:
        get_match_SIL = float(match_SIL.group(1)[1:-1])
        vals['curr_Silence'] = vals['curr_Silence'] + get_match_SIL

    # curr_Distant
    match_MAF = re.search(r'MAF="([^"]+)"', line)
    if match_MAF is not None:
        get_match = float(match_MAF.group(1)[1:-1])
        vals['curr_Distant'] = vals['curr_Distant'] + get_match
    
    match_FAF = re.search(r'FAF="([^"]+)"', line)
    if match_FAF is not None:
        get_match = float(match_FAF.group(1)[2:-1])
        vals['curr_Distant'] = vals['curr_Distant'] + get_match
    
    match_CHF = re.search(r'CHF="([^"]+)"', line)
    if match_CHF is not None:
        get_match = float(match_CHF.group(1)[2:-1])
        vals['curr_Distant'] = vals['curr_Distant'] + get_match

    match_CXF = re.search(r'CXF="([^"]+)"', line)
    if match_CXF is not None:
        get_match = float(match_CXF.group(1)[2:-1])
        vals['curr_Distant'] = vals['curr_Distant'] + get_match

    match_OLF = re.search(r'OLF="([^"]+)"', line)
    if match_OLF is not None:
        get_match = float(match_OLF.group(1)[2:-1])
        vals['curr_Distant'] = vals['curr_Distant'] + get_match

    return vals

def get_epochs(filename, AWC_COUNT, CT_COUNT, CV_COUNT, Meaningful, TV_Secs, Noise, Silence, Distant, Start_Time, End_Time, Exact_Length):
    file = open('/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/itsFiles/' + filename, 'r') # read file .. should be filename like '610LTP1.its'
    lines = file.readlines()

    get_match_start = 0.00
    get_match_end = 0.00

    vals = {'curr_AWC': 0, 'curr_CT': 0, 'curr_CV': 0, 
    'curr_Meaning': 0, 'curr_TV': 0, 'curr_Noise': 0,
    'curr_Silence': 0, 'curr_Distant': 0}

    for line in lines:
        if ("<Conversation " in line) or ("<Pause " in line):
            match_start = re.search(r'startTime="([^"]+)"', line) # format: PT2.47S ... seconds
            if match_start is not None: # should always not be None
                get_match_start = match_start.group(1)[2:-1] # delete first two characters and last character to get the number

            match_end = re.search(r'endTime="([^"]+)"', line)
            if match_end is not None:
                get_match_end = match_end.group(1)[2:-1]

            conversation_length = float(get_match_end) - float(get_match_start)
            vals = get_values(vals, line) # adds to epoch
                
                # push epoch
            AWC_COUNT.append(vals['curr_AWC'])
            CT_COUNT.append(vals['curr_CT'])
            CV_COUNT.append(vals['curr_CV'])
            Meaningful.append(vals['curr_Meaning'])
            TV_Secs.append(vals['curr_TV'])
            Noise.append(vals['curr_Noise'])
            Silence.append(vals['curr_Silence'])
            Distant.append(vals['curr_Distant'])

            Start_Time.append(get_match_start)
            End_Time.append(get_match_end)
            Exact_Length.append(conversation_length)

            # reset values
            vals = {'curr_AWC': 0, 'curr_CT': 0, 'curr_CV': 0, 
                        'curr_Meaning': 0, 'curr_TV': 0, 'curr_Noise': 0,
                        'curr_Silence': 0, 'curr_Distant': 0}
            


# this is a greedy algorithm
# based on "exact_length", each row will have the choice to COMBINE or CUT
# if COMBINE, same row gets to choose again
# if CUT, move to the next row

# COMBINE means merge the second row with the first row (add all values and delete second row)
# CUT means take only 60 seconds, and insert a row right after with remaining seconds
# also 3rd trivial operation, if == 60 seconds, move to next row

# working with lists
def merge(AWC_COUNT, CT_COUNT, CV_COUNT, Meaningful, TV_Secs, Noise, Silence, Distant, Exact_Length):

    i = 0

    # print('merging rows')
    while i < len(AWC_COUNT): # need to calculate new length everytime
        # print('i: ' + str(i))
        # print('len: ' + str(len(AWC_COUNT)))

        #if (i + 1 >= len(AWC_COUNT)): # decide what to do with last one later
        #    return
        
        # look at exact_length to determine CUT or COMBINE
        if Exact_Length[i] == 60:
            i = i + 1
            if i == len(AWC_COUNT): # reached last row
                return
            continue # go to next row

        # COMBINE
        elif (Exact_Length[i] < 60) and ((i+1) < len(AWC_COUNT)): # last row can't perform COMBINE, can't look at next row
            # add everything from next row to current row
            AWC_COUNT[i] += AWC_COUNT[i+1]
            CT_COUNT[i] += CT_COUNT[i+1]
            CV_COUNT[i] += CV_COUNT[i+1]
            Meaningful[i] += Meaningful[i+1]
            TV_Secs[i] += TV_Secs[i+1]
            Noise[i] += Noise[i+1]
            Silence[i] += Silence[i+1]
            Distant[i] += Distant[i+1]
            Exact_Length[i] += Exact_Length[i+1] # important, we need to know the updated time length of the row

            # delete next row
            AWC_COUNT.pop(i+1)
            CT_COUNT.pop(i+1)
            CV_COUNT.pop(i+1)
            Meaningful.pop(i+1)
            TV_Secs.pop(i+1)
            Noise.pop(i+1)
            Silence.pop(i+1)
            Distant.pop(i+1)
            Exact_Length.pop(i+1) # maintain same row numbers

            # don't increment i, want to stay on same row

            continue

        elif Exact_Length[i] > 60: # take just 60 seconds from this row. everything else should be inserted as a new row that comes right after this row

            # save all current values in the row
            temp_AWC = AWC_COUNT[i]
            temp_CT = CT_COUNT[i]
            temp_CV = CV_COUNT[i]
            temp_Mean = Meaningful[i]
            temp_TV = TV_Secs[i]
            temp_Noise = Noise[i]
            temp_Sil = Silence[i]
            temp_Dist = Distant[i]
            temp_Len = Exact_Length[i]

            # calculate 60 seconds / total length for each value
            AWC_COUNT[i] = (60.0 / temp_Len) * temp_AWC
            CT_COUNT[i] = (60.0 / temp_Len) * temp_CT
            CV_COUNT[i] = (60.0 / temp_Len) * temp_CV
            Meaningful[i] = (60.0 / temp_Len) * temp_Mean
            TV_Secs[i] = (60.0 / temp_Len) * temp_TV
            Noise[i] = (60.0 / temp_Len) * temp_Noise
            Silence[i] = (60.0 / temp_Len) * temp_Sil
            Distant[i] = (60.0 / temp_Len) * temp_Dist
            Exact_Length[i] = (60.0 / temp_Len) * temp_Len # roughly 60.0 :)

            # insert new row with remaining values (rest from old row values)
            # .insert(index, value)
            new_AWC = temp_AWC - AWC_COUNT[i]
            new_CT = temp_CT - CT_COUNT[i]
            new_CV = temp_CV - CV_COUNT[i]
            new_Mean = temp_Mean - Meaningful[i]
            new_TV = temp_TV - TV_Secs[i]
            new_Noise = temp_Noise - Noise[i]
            new_Sil = temp_Sil - Silence[i]
            new_Dist = temp_Dist - Distant[i]
            new_Len = temp_Len - 60.0 # extra time

            AWC_COUNT.insert(i+1, new_AWC)
            CT_COUNT.insert(i+1, new_CT)
            CV_COUNT.insert(i+1, new_CV)
            Meaningful.insert(i+1, new_Mean)
            TV_Secs.insert(i+1, new_TV)
            Noise.insert(i+1, new_Noise)
            Silence.insert(i+1, new_Sil)
            Distant.insert(i+1, new_Dist)
            Exact_Length.insert(i+1, new_Len)

            # move to next row. this row is finalized.
            i = i + 1
            continue

        else: # last row may be really small
            return

    # print('done merging rows')


def get_id():
    # get the list of its files from box folder (use path on your local computer)
    path = "/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/itsFiles" # here's where you would specify your path
    true_dir_list = os.listdir(path)

    dir_list = []
    for i in true_dir_list:
        if i.endswith('.its'):
            dir_list.append(i)

    return dir_list # returns file names as a list 


'''
MAIN FUNCTION
'''
def main():
     # get list of filenames from a directory
    all_files = get_id() # returns list of its files in this format: 055LTP1.its
    print(all_files)
    print(len(all_files))
    
    # all_files.append('010LTP2.its')
    # print(all_files) # debugging

# get all the lists --> columns
    for i in range(0, len(all_files)):
        # get all the lists --> columns
        AWC_COUNT = []
        CT_COUNT = []
        CV_COUNT = []
        Meaningful = []
        TV_Secs = []
        Noise = []
        Silence = []
        Distant = []
        Start_Time = []
        End_Time = []
        Exact_Length = []

        # logging
        print('mining file ' + all_files[i])
        
        # mine_its will update all the above lists so we can make a df using them
        get_epochs(all_files[i], AWC_COUNT, CT_COUNT, CV_COUNT, Meaningful, TV_Secs, Noise, Silence, Distant, Start_Time, End_Time, Exact_Length)
        # print(len(AWC_COUNT))
        # print(len(CT_COUNT))
        
        this_file = all_files[i][:-4] # get the id of the file

        merge(AWC_COUNT, CT_COUNT, CV_COUNT, Meaningful, TV_Secs, Noise, Silence, Distant, Exact_Length)

        # num_rows = len(AWC_COUNT)

        df2 = pd.DataFrame({'AWC_COUNT': AWC_COUNT,
                          'CT_COUNT': CT_COUNT, 'CV_COUNT': CV_COUNT,
                             'Meaningful': Meaningful,
                          'TV_Secs': TV_Secs, 'Noise': Noise,
                          'Silence': Silence, 'Distant': Distant,
                          'Exact_Length': Exact_Length})

        df2['id'] = this_file
        df2['Duration_Secs'] = 60.0

        print('making csv file for ' + this_file)
        csv_name = '/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/minute_itsToCSV/' + this_file + '.csv'
        df2.to_csv(csv_name, index=False)

    path = "/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/minute_itsToCSV"
    dir_list = os.listdir(path)

    print(len(dir_list))


# call main
if __name__ == "__main__":
    main()