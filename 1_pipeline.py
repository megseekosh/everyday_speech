from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os
import time

# upload csv files to online classifier
# download them to a specified directory

def classify_file(download_directory, filename, file_counter): #its file name

    # get "Browse..." button id to input file into
    wait = WebDriverWait(driver, 10)
    # wait.until(EC.visibility_of_element_located((By.ID, "dataset")))
    wait.until(EC.presence_of_element_located((By.ID, "dataset"))).send_keys(os.path.join(os.getcwd(), 'minute_itsToCSV', filename))

    #print("inputting data")

    # wait until "download data" button becomes visible, that's how we know the classifier's output file was generated
    wait = WebDriverWait(driver, 60)
    wait.until(EC.element_to_be_clickable((By.ID, "download_button")))
    download_button = driver.find_element(By.ID, "download_data")
    download_button.click()
    #print("downloading data...")

    # check if file is downloaded
    # set time out of 60 seconds (should def take less time)
    max_time = 60
    start = time.time()
    # classifier outputs all files as named: sleep_CDS_classifications.csv
    
    # wait for the file to download
    while not os.path.exists(os.path.join(download_directory, "sleep_CDS_classifications.csv")): 
        if time.time() - start > max_time: # current time compare with start time
            break # maxed out, break and try to download the next file (note this shouldn't really happen)
        time.sleep(3) # give it 3 more seconds to download before you check again

    # rename file based on id column once it has downloaded ... another script to do that 
    if os.path.exists(os.path.join(download_directory, "sleep_CDS_classifications.csv")):
        # since we don't process files in parallel, we can change each sleep_CDS_classifications.csv file to the current filename
        #print("data downloaded")
        os.rename(os.path.join(download_directory, "sleep_CDS_classifications.csv"), os.path.join(download_directory, str(file_counter) + "_sleep_CDS_classifications.csv"))
        #print("file renamed to " + id + "_sleep_CDS_classifications.csv")

def get_csvs():
    csvs = os.listdir("/Users/maduryasuresh/Desktop/SPOG_Lab/minute_itsToCSV")
    #print(csvs)
    return csvs

def check_output():
    classified = os.listdir("/Users/maduryasuresh/Desktop/SPOG_Lab/minute_classify_output")
    print(len(classified))
    print(len(get_csvs()))
    csvs = get_csvs()

    classified_names = []

    for name in classified:
        classified_names.append(name[:-30] + ".csv")

    main_list = list(set(classified_names) - (set(get_csvs())))
    print(main_list)

    if (len(get_csvs()) == len(classified)):
        print('same number of files')
    else:
        print('uh oh... different number of files')

def main():
    global driver

    # set download directory for output
    download_directory = "/Users/maduryasuresh/Desktop/SPOG_Lab/minute_classify_output"
    prefs = {
        "profile.default_content_settings.popups": 0, # block pop ups, like trying to browse a file in finder
        "download.default_directory": download_directory,
        "download.directory_upgrade": True, # automatically renames duplicate files
        "download.prompt_for_download": False
    }

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", prefs) # configure the chrome options for this instance of webdriver (shouldn't change your default chrome browser)

    driver = webdriver.Chrome(options=chrome_options) # chrome webdriver instance, will download to specified path
    driver.implicitly_wait(10)
    driver.get("https://kachergis.shinyapps.io/classify_cds_ods/")

    # call classify_file function
    # arbitrary test file

    filenames = get_csvs()

    file_counter = 0

    for filename in filenames:
        print("started processing " + filename)
        id = filename[:-4]
        classify_file(download_directory, filename, file_counter)
        print("finished processing " + filename)

    # close browser at the end of main
    driver.close()
    driver.quit()

    # check it has quit
    if "(null)" in str(driver):
        print("driver quit")
    else:
        print("driver still running")


if __name__ == "__main__":
    main()