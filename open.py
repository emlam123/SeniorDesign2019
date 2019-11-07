import csv


def get_muscle_data():
    '''
    it opens the csv file and sends the data to the client.
        the given file has 64 columns containing - 8 consecutive readings from 8 sensors. (8 X 8)
    '''
    with open('0.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        linecount = 0
        for row in filereader:
            if linecount == 0:
                linecount += 1
                print(str(linecount) + ' : The columns')
                print(', '.join(row))
            elif linecount < 5:
                linecount += 1
                print(linecount)
                print(', '.join(row))


def Main():
    get_muscle_data()


if __name__ == '__main__':
    Main()
