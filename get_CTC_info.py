import re
import sys
import os
from pydub import AudioSegment
import random
import pandas as pd
import datetime
from lxml import etree
import numpy as np

# def load_audio(audio):
#     init = datetime.datetime.now()
#     print("loading audio")
#     fullAudio = AudioSegment.from_wav(audio)
#     print("audio loaded in ", datetime.datetime.now()-init, " min.sec.ms")
#     return fullAudio
#_______________________________________________________________________________

# def find_all_ct(data, id='1'):
#     print("finding convo. turn chunk timestamps")
#     list_timestamps = []
#     for i in data:
#         m1 = re.findall(r'turnTaking=\"1\"',i) # this needs to be changed to accomodate different nums
#         m2 = re.findall(r'startTime=\"PT([0-9]+\.[0-9]+)S\"', i)
#         m = re.findall(r'endTime=\"PT([0-9]+\.[0-9]+)?S\"', i)
#         if ((m1 != []) & (m != []) & (m2 != [])):
#             list_timestamps.append([m2[0],m[0]])
#     print("list of ct chunk timestamps complete")
#     return list_timestamps

def extract_time(text):
    # removes PT and S characters that surround timestamp strings and converts them to float
    return float(text[2:-1])

def find_all_ct(its_file):
    ct_cnt = [] # count the chunks with <0 turns
    # parse as xml file
    xmldoc = etree.parse(its_file)
    # select all nodes that are segments - I need something else besides segment 
    seg_id = 0
    for seg in xmldoc.iter('Conversation'):
        if (seg.attrib['turnTaking']!='0'):
            # if the # of turns is >0, retrieve the onset and offset of the utterance containing those turns
            # .attrib to get attribute from turnTaking node
            onset = extract_time(seg.attrib['startTime'])
            offset = extract_time(seg.attrib['endTime'])
            duration = offset - onset 
            avg_dB = seg.attrib['average_dB']
            peak_dB = seg.attrib['peak_dB']
            cnt = seg.attrib['turnTaking'] # get the # of convo turns
            its_file_name = its_file[its_file.rfind('/')+1:its_file.rfind('.')]     
            seg_id += 1       
            ct_cnt.append([onset, offset, duration, cnt, avg_dB, peak_dB, its_file_name, seg_id])
    return ct_cnt
#_______________________________________________________________________________

# def create_wav_chunks(timestamps, audio, child_id='child_id'):
#     print("creating wav chunks")
#     output_dir = working_dir+"/"+child_id+'_CTC_output/' # path to the output directory
#     if not os.path.exists(output_dir):
#         os.makedirs(output_dir) # creating the output directory if it does not exist
#     timestamps['total_convo_cts'] = timestamps['convo_count'].groupby(timestamps["clip_onset"]).transform('sum') # in the off chance that there are multiple conversation events within a given minute chunk, add them
#     unq_onset = timestamps.drop_duplicates(['clip_onset','convo_count']) # there will be duplicates if there were multiple events in a given chunk, just get one row
#     for index, ts in unq_onset.iterrows():
#         onset, offset, duration, count = ts['clip_onset'], ts['clip_offset'], ts['duration'], ts['total_convo_cts'] # most cases total and convo count will be same
#         #new_audio_chunk = audio[onset*1000:offset*1000] # if we wanted to index by onset, offset and get individual vocalizations
#         convo_chunk = audio[onset*1000:offset*1000] # TODO: need to multiply by 1000?
#         convo_chunk.export("{}{}_{}_{}_{}.wav".format(output_dir, int(count), onset, offset, child_id), format("wav"), bitrate="192k")

#_______________________________________________________________________________

def list_to_csv(list_ts, output_file): # to remember intermediaries
    #df = pd.DataFrame(list_ts, columns=["onset", "offset"]) # df of timestamps
    list_ts.to_csv(working_dir+"/"+filename+"_CTC_output") # write dataframe to file
#_______________________________________________________________________________

def process_one_file(its):

    all_ct_timestamps = []

    if isinstance(its,list): # for multiple its files/day
        for i in range(len(its)):
            all_ct_timestamps += find_all_ct(its[i]) # index each element of its array
    else: # for 1 its file/day
            all_ct_timestamps = find_all_ct(its)
  
    df2 = pd.DataFrame(all_ct_timestamps, columns=["onset", "offset", "duration", "convo_count", "avg_dB", "peak_dB", "its_file_name", "seg_id"]) # df of timestamps
    df2['offset'] = pd.to_numeric(df2['offset']) 
    df2['seconds'] = ((df2['offset'] // 60)*60)+60  # create a column of 'seconds'

    df2.columns = ['clip_onset', 'clip_offset', "duration", 'convo_count', "avg_dB", "peak_dB", 'its_file_name', 'seg_id', 'seconds']

    list_to_csv(df2,filename+"_"+"CTC_timestamps.csv")
       
#_______________________________________________________________________________

if __name__ == "__main__":

    # to run one child at a time
    # working_dir = sys.argv[1]
    # filename = sys.argv[2]
    # child_id = filename[0:7]
    # audio_file = working_dir+"/"+filename+'.wav'
    # its_file = working_dir+"/"+filename+'.its' 

    # otherwise to batch process
    working_dir = __file__
    working_dir = working_dir[0:working_dir.rfind('/')] # find the last slash in filepath and cut off after that 
    
    processed_files = []
    for f in sorted(os.listdir(working_dir)):
        if f.endswith(".its") and f not in processed_files:
            print(f)
            filename = f[0:f.rfind('.')] # everything before the extension
            its_file = working_dir+"/"+filename+'.its' 
            process_one_file(its_file) # process one child at a time
            processed_files.append(filename) # append to list after processing


        if f[-6]=='_':         # if there are several files from the same day
            its_files = [its_file]
            for filename_other in os.listdir(working_dir):
                if filename_other.endswith('.its') and f[:-6]==filename_other[:-6] and f[-5]!=filename_other[-5]:
                    its_files.append(working_dir+"/"+filename_other)
            process_one_file(its_files)
            for file in its_files:
                print('processing', file)
                processed_files.append(file) # append to list after processing
            else:
                print('processing', f)
                process_one_file(its_file)
                processed_files.append(f) # append to list after processing