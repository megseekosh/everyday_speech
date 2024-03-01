import re
import pandas as pd
import os

# mine 5-minute epochs from the its files
# LENA provides the 5 minute epochs, with fields for each, at the bottom of each its file
# mine this info, and put it in a df that is in the correct format to input into the cds/sleep classifier

'''
HELPER FUNCTIONS
'''

''' 
mine_its function
    gets all the information from the five minute segments in the its file
    compiles the information into separate lists, which will become columns in the df
'''
def mine_its(filename, id, AWC_COUNT, CT_COUNT, CV_COUNT, Duration_Secs, Meaningful, TV_Secs, Noise, Silence, Distant):
    file = open('/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/itsFiles/' + filename, 'r') # read file .. should be filename like '610LTP1.its'
    lines = file.readlines() # get lines

    count = 0

    for line in lines:
        if "<FiveMinuteSection" in line: # these are the lines we want to look at
            count += 1

            # get AWC
            # use regex
            match1 = re.search(r' maleAdultWordCnt="([^"]+)"', line) # need to put a space in front of male, otherwise it will match with female because it appears first
            match2 = re.search(r'femaleAdultWordCnt="([^"]+)"', line)
            match1_sec = (match1.group(1)) # in the form 138.68
            match2_sec = (match2.group(1))
            #print('match1: ' + match1_sec)
            #print('match2: ' + match2_sec)
            total_awc = str(float(match1_sec) + float(match2_sec))
            #print('total: ' + total_awc)
            AWC_COUNT.append(total_awc)

            # get CT_COUNT
            match = re.search(r'turnTaking="([^"]+)"', line)
            CT_COUNT.append(match.group(1))

            # get CV_COUNT
            match = re.search(r'childUttCnt="([^"]+)"', line)
            CV_COUNT.append(match.group(1))

            # get Meaningful (duration)
            # this data is in the following format: ISO 8601 standard P58.73S, meaning 58.73 seconds
                # so, we need to remove first and last characters and add as floats
            match1 = re.search(r'MAN="([^"]+)"', line)
            match1_sec = (match1.group(1))[1:-1] # delete first and last characters
            match2 = re.search(r'FAN="([^"]+)"', line)
            match2_sec = (match2.group(1))[1:-1]
            match3 = re.search(r'CHN="([^"]+)"', line)
            match3_sec = (match3.group(1))[1:-1]
            match4 = re.search(r'CXN="([^"]+)"', line)
            match4_sec = (match4.group(1))[1:-1]
            total_meaningful = str(float(match1_sec) + float(match2_sec) + float(match3_sec) + float(match4_sec)) # cast to float add the numbers
            Meaningful.append(total_meaningful)

            # get TV_Secs
            match1 = re.search(r'TVN="([^"]+)"', line)
            match1_sec = (match1.group(1))[1:-1]
            total_tv = str(float(match1_sec))
            TV_Secs.append(total_tv)

            # get Noise
            match1 = re.search(r'NON="([^"]+)"', line)
            match1_sec = (match1.group(1))[1:-1]
            total_noise = str(float(match1_sec))
            Noise.append(total_noise)

            # get Silence
            match = re.search(r'SIL="([^"]+)"', line)
            match_sec = (match.group(1))[1:-1]
            Silence.append(match_sec)

            # get Distant
            match1 = re.search(r'MAF="([^"]+)"', line)
            match2 = re.search(r'FAF="([^"]+)"', line)
            match3 = re.search(r'CXF="([^"]+)"', line)
            match4 = re.search(r'CHF="([^"]+)"', line)
            match5 = re.search(r'OLF="([^"]+)"', line)
            match1_sec = (match1.group(1))[1:-1]
            match2_sec = (match2.group(1))[1:-1]
            match3_sec = (match3.group(1))[1:-1]
            match4_sec = (match4.group(1))[1:-1]
            match5_sec = (match5.group(1))[1:-1]
            total_distant = str(float(match1_sec) + float(match2_sec) + float(match3_sec) + float(match4_sec) + float(match5_sec))
            Distant.append(total_distant)

    # get Duration_Secs
    # fill an array of size "count" with 300 seconds (count says how many five minute segments there are)
    for i in range(0, count):
        Duration_Secs.append(300) # 5 min segments, so fill as all 5s

    # create column ids from file name (child's id), which should be the filename with '.its', final 4 characters removed
    for i in range(0, count):
        id.append(filename[:-4]) # column name ... remove '.its' from end of filename to get the id of child + recording

'''
get_id function
    takes in a string representing file path
    outputs just the actual file name
'''
def get_id():
    # get the list of its files from box folder (use path on your local computer)
    path = "/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/itsFiles" # here's where you would specify your path
    dir_list = os.listdir(path)

    return dir_list # returns file names as a list 





'''
MAIN
'''

'''
main function
    batch processing based on file names in a specified directory full of its files
'''
def main():
    # get list of filenames from a directory
    all_files = get_id() # returns list of its files in this format: 055LTP1.its
    print(all_files)
    # return
    #print(all_files) # debugging

# get all the lists --> columns
    for i in range(0, len(all_files)):
        # get all the lists --> columns
        id = []
        AWC_COUNT = []
        CT_COUNT = []
        CV_COUNT = []
        Meaningful = []
        TV_Secs = []
        Noise = []
        Silence = []
        Distant = []
        Duration_Secs = []

        # logging
        print('mining file ' + all_files[i])
        
        # mine_its will update all the above lists so we can make a df using them
        mine_its(all_files[i], id, AWC_COUNT, CT_COUNT, CV_COUNT, Duration_Secs, Meaningful, TV_Secs, Noise, Silence, Distant)
        df = pd.DataFrame({'id': id, 'AWC_COUNT': AWC_COUNT,
                          'CT_COUNT': CT_COUNT, 'CV_COUNT': CV_COUNT,
                          'Duration_Secs': Duration_Secs, 'Meaningful': Meaningful,
                          'TV_Secs': TV_Secs, 'Noise': Noise,
                          'Silence': Silence, 'Distant': Distant})

        this_file = all_files[i][:-4] # get the id of the file
        print('creating csv for ' + this_file)  # logging
        csv_name = '/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/minute_itsToCSV/' + this_file + '.csv' # output it into specified folder with correct name
        df.to_csv(csv_name, index=False)



# call main
if __name__ == "__main__":
    main()






'''
['800ECV2', '115RTP4', '014LTP2', '683LTP1', '004LTP2', '107LTP1', '117LTP1', '104RTP1', '114RTP1', '122RTP3', '507M', '140RTP3', '166RTP1', '176RTP1', '648LTP1', '658LTP1', '511M', '076LTP2', '623LTP2', '040LTP1', '128LTP1', '092LTP2', '605LTP1', '082LTP2', '456D', '182RTP1', '140RTP2', '440D', '122RTP2', '049LTP2', '007JTP2', '121LTP2', '677LTP1', '667LTP1', '022LTP1', '032LTP1', '159RTP1', '149RTP1', '149RTP3', '641LTP1', '683LTP2', '014LTP1', '117LTP2', '107LTP2', '114RTP2', '104RTP2', '176RTP2', '166RTP2', '076LTP1', '633LTP1', '802ECV1', '623LTP1', '128LTP2', '050LTP2', '040LTP2', '082LTP1', '151RTP4', '605LTP2', '141RTP4', '166RTP3', '182RTP2', '140RTP1', '122RTP1', '114RTP3', '059LTP1', '121LTP1', '049LTP1', '017JTP1', '131LTP1', '133RTP4', '667LTP2', '123RTP4', '032LTP2', '022LTP2', '303ECV1', '149RTP2', '159RTP2', '106LTP2', '116LTP2', '105RTP2', '115RTP2', '015LTP1', '005LTP1', '640LTP1', '632LTP1', '077LTP1', '067LTP1', '167RTP2', '177RTP2', '151RTP1', '141RTP1', '614LTP2', '093LTP1', '140RTP4', '604LTP2', '083LTP1', '041LTP2', '051LTP2', '129LTP2', '023LTP2', '033LTP2', '158RTP2', '302ECV1', '312ECV1', '115RTP3', '133RTP1', '123RTP1', '130LTP1', '058LTP1', '116LTP1', '106LTP1', '133RTP3', '123RTP3', '115RTP1', '105RTP1', '005LTP2', '015LTP2', '441D', '166RTP4', '622LTP2', '067LTP2', '077LTP2', '457D', '177RTP1', '167RTP1', '151RTP3', '141RTP3', '659LTP1', '141RTP2', '151RTP2', '510M', '083LTP2', '604LTP1', '093LTP2', '614LTP1', '129LTP1', '051LTP1', '041LTP1', '033LTP1', '023LTP1', '666LTP1', '506M', '158RTP1', '312ECV2', '302ECV2', '123RTP2', '133RTP2', '149RTP4', '058LTP2', '130LTP2', '128RTP3', '065LTP1', '075LTP1', '630LTP1', '620LTP1', '801ECV1', '689LTP1', '175RTP2', '165RTP2', '431D', '117RTP2', '107RTP2', '114LTP2', '104LTP2', '427D', '629LTP2', '652LTP1', '642LTP1', '007LTP1', '300ECV1', '120RTP4', '031LTP2', '021LTP2', '122LTP1', '132LTP1', '088LTP2', '098LTP2', '121RTP1', '131RTP1', '117RTP3', '165RTP3', '181RTP2', '143RTP1', '153RTP1', '038LTP1', '028LTP1', '053LTP2', '043LTP2', '081LTP1', '616LTP2', '142RTP4', '128RTP2', '075LTP2', '065LTP2', '620LTP2', '164RTP4', '689LTP2', '143RTP3', '165RTP1', '175RTP1', '501M', '107RTP1', '117RTP1', '121RTP3', '131RTP3', '104LTP1', '114LTP1', '629LTP1', '808ECV1', '639LTP1', '116RTP4', '017LTP2', '007LTP2', '680LTP1', '674LTP1', '664LTP1', '021LTP1', '031LTP1', '122LTP2', '450D', '098LTP1', '088LTP1', '131RTP2', '121RTP2', '309ECV1', '181RTP1', '153RTP2', '143RTP2', '129RTP4', '139RTP4', '038LTP2', '043LTP1', '411D', '053LTP1', '616LTP1', '081LTP2', '128RTP1', '174RTP1', '164RTP1', '142RTP3', '447D', '165RTP4', '631LTP2', '064LTP2', '074LTP2', '681LTP1', '006LTP2', '016LTP2', '117RTP4', '451D', '130RTP3', '120RTP3', '116RTP1', '106RTP1', '638LTP1', '628LTP1', '809ECV1', '089LTP1', '099LTP1', '123LTP2', '133LTP2', '120RTP2', '130RTP2', '301ECV2', '030LTP1', '020LTP1', '665LTP1', '607LTP1', '080LTP2', '090LTP2', '052LTP1', '042LTP1', '500M', '129RTP1', '139RTP1', '142RTP2', '180RTP1', '308ECV1', '039LTP2', '029LTP2', '128RTP4', '688LTP1', '164RTP2', '174RTP2', '129RTP3', '139RTP3', '631LTP1', '074LTP1', '064LTP1', '016LTP1', '006LTP1', '106RTP2', '116RTP2', '628LTP2', '023JTP2', '099LTP2', '089LTP2', '133LTP1', '123LTP1', '116RTP3', '130RTP1', '120RTP1', '426D', '301ECV1', '311ECV1', '020LTP2', '030LTP2', '121RTP4', '131RTP4', '665LTP2', '090LTP1', '143RTP4', '607LTP2', '042LTP2', '052LTP2', '139RTP2', '129RTP2', '142RTP1', '180RTP2', '164RTP3', '029LTP1', '039LTP1', '113RTP3', '125RTP1', '135RTP1', '126LTP1', '010JTP1', '035LTP2', '025LTP2', '134RTP4', '448D', '314ECV1', '304ECV1', '085LTP1', '602LTP2', '095LTP1', '612LTP2', '057LTP2', '669LTP1', '679LTP1', '147RTP1', '161RTP3', '171RTP2', '161RTP2', '634LTP1', '805ECV1', '425D', '624LTP1', '061LTP1', '119LTP1', '109LTP1', '433D', '168RTP1', '656LTP1', '646LTP1', '110LTP2', '068LTP2', '100LTP2', '078LTP2', '113RTP2', '103RTP2', '135RTP2', '125RTP2', '010JTP2', '126LTP2', '025LTP1', '035LTP1', '670LTP1', '660LTP1', '304ECV2', '314ECV2', '444D', '612LTP1', '095LTP2', '602LTP1', '085LTP2', '057LTP1', '679LTP2', '147RTP2', '161RTP1', '171RTP1', '147RTP3', '392A', '624LTP2', '160RTP4', '515M', '109LTP2', '071LTP2', '119LTP2', '061LTP2', '503M', '168RTP2', '684LTP1', '078LTP1', '100LTP1', '125RTP3', '135RTP3', '103RTP1', '113RTP1', '661LTP1', '671LTP1', '034LTP1', '024LTP1', '305ECV2', '124RTP2', '134RTP2', '001JTP2', '127LTP2', '502M', '428D', '678LTP2', '146RTP2', '056LTP1', '046LTP1', '084LTP2', '603LTP1', '094LTP2', '118LTP2', '108LTP2', '161RTP4', '625LTP2', '453D', '170RTP1', '160RTP1', '045JTP1', '111LTP1', '069LTP1', '101LTP1', '079LTP1', '445D', '112RTP1', '102RTP1', '134RTP3', '179RTP2', '169RTP2', '113RTP4', '002LTP2', '685LTP1', '012LTP2', '661LTP2', '135RTP4', '024LTP2', '034LTP2', '305ECV1', '134RTP1', '124RTP1', '127LTP1', '678LTP1', '668LTP1', '424D', '160RTP3', '146RTP1', '046LTP2', '056LTP2', '613LTP2', '094LTP1', '147RTP4', '603LTP2', '084LTP1', '108LTP1', '118LTP1', '060LTP1', '804ECV1', '625LTP1', '160RTP2', '170RTP2', '101LTP2', '069LTP2', '111LTP2', '102RTP2', '112RTP2', '169RTP1', '179RTP1', '657LTP1', '012LTP1', '685LTP2', '154RTP2', '144RTP2', '096LTP2', '611LTP1', '086LTP2', '044LTP1', '119RTP3', '442D', '036LTP1', '673LTP1', '454D', '608LTP2', '013JTP2', '136RTP2', '136RTP3', '100RTP1', '110RTP1', '613LTP1b', '103LTP1', '113LTP1', '513M', '010LTP2', '505M', '119RTP2', '627LTP2', '439D', '072LTP2', '019LTP1', '009LTP1', '162RTP1', '172RTP1', '144RTP3', '154RTP3', '144RTP1', '154RTP1', '162RTP3', '086LTP1', '611LTP2', '145RTP4', '096LTP1', '044LTP2', '307ECV1', '137RTP4', '127RTP4', '608LTP1', '125LTP1', '136RTP1', '110RTP2', '100RTP2', '113LTP2', '103LTP2', '423D', '010LTP1', '655LTP1', '119RTP1', '109RTP1', '806ECV1', '062LTP1', '072LTP1', '009LTP2', '019LTP2', '118RTP4', '172RTP2', '162RTP2', '055LTP2', '097LTP1', '144RTP4', '610LTP2', '154RTP4', '087LTP1', '600LTP2', '145RTP1', '434D', '134LTP1', '124LTP1', '609LTP1', '137RTP1', '422D', '127RTP1', '306ECV1', '092LTP1b', '136RTP4', '037LTP2', '644LTP1', '654LTP1', '011LTP1', '001LTP1', '686LTP2', '101RTP2', '111RTP2', '112LTP2', '459D', '119RTP4', '018LTP2', '008LTP2', '163RTP2', '173RTP2', '118RTP1', '073LTP1', '063LTP1', '418D', '807ECV1', '636LTP1', '055LTP1', '045LTP1', '600LTP1', '087LTP2', '610LTP1', '097LTP2', '118RTP3', '145RTP2', '504M', '124LTP2', '609LTP2', '127RTP2', '137RTP2', '037LTP1', '686LTP1', '001LTP2', '011LTP2', '111RTP1', '101RTP1', '137RTP3', '127RTP3', '455D', '112LTP1', '102LTP1', '008LTP1', '443D', '018LTP1', '145RTP3', '173RTP1', '163RTP1', '118RTP2', '063LTP2', '162RTP4']

'''
