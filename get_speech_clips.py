# identifies all MAN, FAN, and overlap (FAN-OLN-CHN or CHN-OLN-FAN)
# from LENA .its file and affiliated .wav file 
# with basic acoustics and timestamps
# and spits out identified audio files
# into speaker-specific directories
# childID and segment type (MAN, FAN, or OLN) must be specified in command line

import re
import sys
import os
from pydub import AudioSegment
from pydub.utils import make_chunks
import random
import pandas as pd
import datetime
from lxml import etree
import numpy as np

def load_audio(audio):
    init = datetime.datetime.now()
    print("loading audio")
    fullAudio = AudioSegment.from_wav(audio)
    print("audio loaded in ", datetime.datetime.now()-init, " min.sec.ms")
    return fullAudio
#_______________________________________________________________________________

# def find_all_fan(data, id='FAN'):
#     print("finding FAN timestamps")
#     list_timestamps = []
#     for i in data:
#         s = re.findall(r'spkr=\"FAN\"',i) # m1
#         t1 = re.findall(r'startTime=\"PT([0-9]+\.[0-9]+)S\"', i) # m2
#         t2 = re.findall(r'endTime=\"PT([0-9]+\.[0-9]+)?S\"', i) # m
#         avg_dB = re.findall(r'average_dB=\"PT([0-9]+\.[0-9]+)?S\"', i) 
#         peak_dB = re.findall(r'peak_dB=\"PT([0-9]+\.[0-9]+)?S\"', i) 
#         wordCount = re.findall(r'femaleAdultWordCnt=\"PT([0-9]+\.[0-9]+)?S\"', i) 
#         if ((s != []) & (t2 != []) & (t1 != [])):
#             list_timestamps.append([t1[0],t2[0],avg_dB[0],peak_dB[0],wordCount[0]])
#     print("list of fan timestamps complete")
#     print(list_timestamps)
#     return list_timestamps

def extract_time(text):
    # removes PT and S from timestamp string and converts it to float
    return float(text[2:-1])

def find_all_speech(its_file):
    utt = []
    # parse as xml file
    xmldoc = etree.parse(its_file)
    # select all nodes that are segments
    seg_id = 0
    for seg in xmldoc.iter('Segment'):
    # print(str(seg))
        if (seg.attrib['spkr']==segment):

            if segment=='FAN':
                wordCount = seg.attrib['femaleAdultWordCnt']
                nonSpeechDur = seg.attrib['femaleAdultNonSpeechLen']
                uttCnt = seg.attrib['femaleAdultUttCnt']
                uttLength = seg.attrib['femaleAdultUttLen']
            elif segment=='MAN':
                wordCount = seg.attrib['maleAdultWordCnt']
                nonSpeechDur = seg.attrib['maleAdultNonSpeechLen']
                uttCnt = seg.attrib['maleAdultUttCnt']
                uttLength = seg.attrib['maleAdultUttLen']
            else:
                wordCount = 'NA'
                nonSpeechDur = 'NA'
                uttCnt = 'NA'
                uttLength = 'NA'

            if (segment=='OLN' or segment=='OLF') and (extract_time(seg.attrib['endTime'])-extract_time(seg.attrib['startTime'])) > 10:
                onset = extract_time(seg.attrib['startTime'])
                offset = extract_time(seg.attrib['endTime'])
                duration = offset-onset
                num_clips = list(range(int(duration)//3)) # number of clips within the larger clip
                for n in num_clips:
                    new_onset = n*3 + onset
                    new_offset = new_onset + 3
                    if n == num_clips[-1]: # for the last clip
                        new_offset = offset
                    else: 
                        new_offset = new_onset + 3 
                    new_duration = new_offset - new_onset
                    avg_dB = seg.attrib['average_dB']
                    peak_dB = seg.attrib['peak_dB']
                    file_name = '{}_{}_{}_{}.wav'.format(int(new_onset), int(new_offset), segment, child_id)
                    seg_id += 1
       
                    utt.append([seg_id, new_onset, new_offset, new_duration, avg_dB, peak_dB, file_name])

            else:
                onset = extract_time(seg.attrib['startTime'])
                offset = extract_time(seg.attrib['endTime'])
                duration = offset - onset
                avg_dB = seg.attrib['average_dB']
                peak_dB = seg.attrib['peak_dB']
                file_name = '{}_{}_{}_{}.wav'.format(int(onset), int(offset), segment, child_id)
                seg_id += 1

                utt.append([seg_id, onset, offset, duration, avg_dB, peak_dB, wordCount, nonSpeechDur, uttCnt, uttLength, file_name])

           
    return utt
#_______________________________________________________________________________

def create_wav_chunks(timestamps, audio, child_id='child_id'):
    print("creating wav chunks")
    output_dir = working_dir+"/"+child_id+'_speech_output/' # path to the output directory
    # audio_file_id = audio_file.split('/')[-1][:-4]
    #unq_seconds = pd.DataFrame({'seconds':timestamps.seconds.unique()})
    #unq_seconds = timestamps.drop_duplicates(['seconds','wordCount'])
    for i, (index, ts) in enumerate(timestamps.iterrows()): # unique # of voc and timestamp here
        if i == len(timestamps) - 1: # skip the last row because it's nans
            pass
        else:
            onset, offset, seconds = ts['clip_onset'], ts['clip_offset'], ts['seconds']
            if ts["segment_type"]=='OLN' and offset-onset>10:
                num_clips = list(range(0,int((offset-onset)/3))) # how many little clips in the big clip
                for n in num_clips:
                    new_onset = n*3 + onset
                    if n==num_clips[-1]: # for the last clip
                        new_offset = offset
                    else:
                        new_offset = new_onset + 3
                small_audio_chunk = audio[int(new_onset)*1000:int(new_offset)*1000] 
                small_audio_chunk.export("{}{}_{}_{}_{}.wav".format(output_dir, int(new_onset), int(new_offset), segment, child_id), format("wav"),bitrate="192k")
            else: 
                new_audio_chunk = audio[int(onset)*1000:int(offset)*1000] # if we want to index by onset, offset and get individual speech events
                # one_minute_chunk = audio[(int(seconds)-60)*1000:int(seconds)*1000] # if we want to get minute-long recordings
                new_audio_chunk.export("{}{}_{}_{}_{}.wav".format(output_dir, int(onset), int(offset), segment, child_id), format("wav"),bitrate="192k")

#_______________________________________________________________________________

def list_to_csv(list_ts, output_file_name): # to remember intermediaries
    #df = pd.DataFrame(list_ts, columns=["onset", "offset"]) # df of timestamps
    list_ts.to_csv(working_dir+"/"+child_id+'_speech_output/'+output_file_name) # write dataframe to file
    #list_ts.to_csv(working_dir+"/"+output_file_name) # write dataframe to general directory
#_______________________________________________________________________________

def process_one_file(its, audio):
#def process_one_file(its):

    # the following code assumes only 1 .its file/recording
    # and will need to be updated if there are ever > 1
    #full_audio = []
    #for audio in audio_files:
    #    full_audio = load_audio(audio)
    
    #full_audio = load_audio(audio)

    all_timestamps = []
    all_timestamps += find_all_speech(its)

    df2 = pd.DataFrame(all_timestamps, columns=["seg_id", "onset", "offset", "duration", "avg_dB", "peak_dB", "wordCount", "nonSpeechDur", "uttCnt", "uttLength", "file_name"]) # df of timestamps
    df2['offset'] = pd.to_numeric(df2['offset']) 
    df2['seconds'] = ((df2['offset'] // 60)*60)+60  # create a column of 'seconds'
    df2['child'] = child_id
    df2['segment_type'] = segment
    df2['random_idx'] = np.random.choice(range(len(df2)), len(df2), replace=False)

    df2.columns = ["seg_id",'clip_onset', 'clip_offset', "duration", "avg_dB", "peak_dB", "wordCount", "nonSpeechDur", "uttCnt", "uttLength", "file_name", "seconds", "child_id", "segment_type", "random_idx"]

    list_to_csv(df2, child_id+"_"+segment+"_"+"timestamps.csv")

    create_wav_chunks(df2, full_audio, child_id)
#_______________________________________________________________________________

if __name__ == "__main__":


    working_dir = __file__
    working_dir = working_dir[0:working_dir.rfind('/')] # find the last slash in filepath and cut off after that 
    # to run one child at a time 
    #filename = sys.argv[1]
    #segment = sys.argv[2] # FAN, MAN, OLN, or OLF
    #child_id = filename[0:7]
    #audio_file = working_dir+"/"+filename+'.wav'
    #its_file = working_dir+"/"+filename+'.its' 
    #output_dir = working_dir+"/"+child_id+'_speech_output/' # path to the output directory
    #if os.path.exists(its_file): 
    #    if not os.path.exists(output_dir):
    #        os.mkdir(output_dir) # creating the output directory if it does not exist
    #process_one_file(its_file, audio_file)
    #process_one_file(its_file)

  # otherwise to batch process
    segment = sys.argv[1] # FAN, MAN, OLN, or OLF
    
    processed_files = []
    its_files = []
    # audio_files = []
    for f in sorted(os.listdir(working_dir)):
        if f.endswith(".its") and f not in processed_files:
            child_id = f[0:7]
            metadata_df = working_dir+"/"+child_id+'_speech_output/'+child_id+'_'+segment+'_timestamps.csv'
            #if not os.path.exists(metadata_df): # if there isn't a metadata sheet for this recording*segment, process the recording; else skip
            filename = f[0:f.rfind('.')] # everything before the extension
            audio_file = working_dir+"/"+filename+'.wav'
            its_file = working_dir+"/"+filename+'.its' 
            output_dir = working_dir+"/"+child_id+'_speech_output/' # path to the output directory
            if os.path.exists(its_file): 
                if not os.path.exists(output_dir):
                    os.mkdir(output_dir) # creating the output directory if it does not exist
                 
                #if f[-6]=='_':         # if there are several files from the same day; this code will currently not work for audio
                    #its_files = [its_file]
#                    audio_files = [audio_file]
                    #for filename_other in os.listdir(working_dir):
                         #if filename_other.endswith('.its') and f[:-6]==filename_other[:-6] and f[-5]!=filename_other[-5]:
                             #its_files.append(working_dir+"/"+filename_other)
#                    process_one_file(its_files, audio_files)
                #process_one_file(its_file)
                for file in its_files:
                    print('processing', file)
                    processed_files.append(file) # append to list after processing
                else:
                     print('processing', f)
                     process_one_file(its_file, audio_file)
                     #process_one_file(its_file)
                     processed_files.append(f) # append to list after processing
            #else:
                #print('already processed',segment,'clips for', child_id)