import pandas as pd
import os

def get_csvs():
    path = "/Users/maduryasuresh/Desktop/SPOG_Lab/minute_classify_output"
    li  = os.listdir(path)

    dir_csvs = []

    for i in li:
        if i.endswith('.csv'):
            dir_csvs.append(i)
    
    return dir_csvs

# change filename to id
def replace_filename(df):
    # first_entry = df['Name'].iloc[0]

    id = df['id'].iloc[0]
    print('replacing ' + id)

    return id

# check all files were sent through the pipeline
def same_files():
    its = os.listdir("/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/itsFiles")
    classified = os.listdir("/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/minute_classified")
    csv = os.listdir("/Users/maduryasuresh/Library/CloudStorage/Box-Box/box-group-lena-studies/Soundscape/minute_itsToCSV")

    its_e = []
    csv_e = []
    classified_e = []

    for i in its:
        if i.endswith(".its"):
            its_e.append(i[:-4])
    
    for i in csv:
        if i.endswith(".csv"):
            csv_e.append(i[:-4])

    for i in classified:
        if i.endswith(".csv"):
            classified_e.append(i[:-32])

    its_s = set(its_e)
    csv_s = set(csv_e)
    classified_s = set(classified_e)

    print(its_s - csv_s)
    print(csv_s - its_s)
    print(its_s - classified_s)
    print(classified_s - its_s)
    print(csv_s - classified_s)
    print(classified_s - csv_s)

    print(len(its_s))
    print(len(csv_s))
    print(len(classified_s))

def main():
    
    dir_csvs = get_csvs()

    for file in dir_csvs:
        df = pd.read_csv("/Users/maduryasuresh/Desktop/SPOG_Lab/minute_classify_output/" + file)
        id = replace_filename(df)
        df.to_csv("/Users/maduryasuresh/Desktop/SPOG_Lab/minute_classified/" + id + "_minute_sleep_CDS_classified.csv", index=False)
        print('new file ' + id + "_minute_sleep_CDS_classified.csv")
    

    same_files() # checks all files went through pipeline correctly

if __name__ == "__main__":
    main()