import re
import sys
import os
from pydub import AudioSegment
import random
import pandas as pd
import datetime
from lxml import etree
import numpy as np


#_______________________________________________________________________________
def get_info(its_file):
    child_info = []
    all_rec_info = []
    xmldoc = etree.parse(its_file)
    # select all nodes that are segments
    for seg in xmldoc.iter('ChildInfo'):
        DOB = seg.attrib['dob']
        gender = seg.attrib['gender']
        age = seg.attrib['chronologicalAge'][1:3]
        child_info.append([DOB, gender, age])
    for s in xmldoc.iter('Recording'):
        startClockTime = s.attrib['startClockTime']
        endClockTime = s.attrib['endClockTime']
        startTimeSecs = s.attrib['startTime'][2:]
        endTimeSecs = s.attrib['endTime'][2:]
        all_rec_info.append([startClockTime, endClockTime, startTimeSecs,endTimeSecs])
    all_info = child_info[0] + all_rec_info[0]
    return all_info

#_______________________________________________________________________________

def list_to_csv(list_ts, output_file): # to remember intermediaries
    list_ts.to_csv(working_dir+"/"+child_id+"_speech_output/"+output_file) # write dataframe to file
#_______________________________________________________________________________

def process_one_file(its):

    all_info = []
    all_info += get_info(its) 

    df2 = pd.DataFrame([all_info], columns=["DOB", "gender", "age_mos", "startClockTime", "endClockTime", "startTimeSecs", "endTimeSecs"]) 
    df2['child_id'] = child_id
    df2['filename'] = its

    #if len(sys.argv)>2:
    list_to_csv(df2,child_id+"_"+"its_info.csv")

#_______________________________________________________________________________

if __name__ == "__main__":

    working_dir = __file__
    working_dir = working_dir[0:working_dir.rfind('/')] # find the last slash in filepath and cut off after that 

    # to run one child at a time
    #filename = sys.argv[1]
    #child_id = filename[0:7]
    #its_file = working_dir+"/"+filename+'.its' 
    #output_dir = working_dir+"/"+child_id+'_speech_output/' # path to the output directory
    #if not os.path.exists(output_dir):
    #    os.mkdir(output_dir) # creating the output directory if it does not exist
    #process_one_file(its_file) # process one child at a time

    # otherwise to batch process

    processed_files = []
    for f in sorted(os.listdir(working_dir)):
        if f.endswith(".its") and f not in processed_files:
            print(f)
            child_id = f[0:7]
            metadata_df = working_dir+"/"+child_id+'_speech_output/'+child_id+'_its_info.csv'
            if not os.path.exists(metadata_df): # if there isn't a metadata its sheet for this its file, process the file; else skip
                filename = f[0:f.rfind('.')] # everything before the extension
                output_dir = working_dir+"/"+child_id+'_speech_output/' # path to the output directory
                if os.path.exists(f): 
                    if not os.path.exists(output_dir):
                        os.mkdir(output_dir) # creating the output directory if it does not exist
                    process_one_file(f) # process one child at a time
                    print('processing', f)
                    processed_files.append(f) # append to list after processing
            else:
                print('already processed .its file for', child_id)

        # if there are several files from the same day
        # if filename[-6]=='_':
        #     for filename_other in os.listdir(working_dir):
        #          if filename_other.endswith('.its') and filename[:-6]==filename_other[:-6] and filename[-5]!=filename_other[-5]:
        #              its_files.append(working_dir+"/"+filename_other)
        #              audio_files.append(working_dir+"/"+filename_other[:-4]+".wav")
        #              processed_files.append(filename_other)
    #process_one_file(its_file)