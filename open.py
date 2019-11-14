import csv
import queue

MEMORYSIZE = 35
STORAGE = queue.Queue(maxsize=MEMORYSIZE)

def get_muscle_data():
    '''
    it opens the csv file and stores the data into a queue.
        When the queue is full, it writes its value to the output csv file then empties the queue.
            the input file has 64 columns containing - 8 consecutive readings from 8 sensors. (8 X 8)
    '''

    with open('0.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        linecount = 0
        colcount = 0;
        for row in filereader:
            if(linecount < 100):
                linecount += 1
                if not STORAGE.full():
                    print(row[0].split(',')[0])
                    STORAGE.put(row[0].split(',')[0])
                else:
                    with open('outputData.csv', 'a') as fd:
                        while not STORAGE.empty():
                            fd.write(STORAGE.get()+'\n')





def Main():

##    while True:
        get_muscle_data()





if __name__ == '__main__':
    Main()
