import csv

<<<<<<< HEAD
def get_muscle_data():
    ''' it opens the csv file and sends the data to the client.'''
=======

def get_muscle_data():
    '''
    it opens the csv file and sends the data to the client.
        the given file has 64 columns containing - 8 consecutive readings from 8 sensors. (8 X 8)
    '''
>>>>>>> 09a475b0cd1c3c2f7a51f9da16b0ede4f29ade86
    with open('0.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        linecount = 0
        for row in filereader:
<<<<<<< HEAD
            if(linecount == 0):
                linecount += 1
                print(str(linecount)+ ' : The columns')
                print(', '.join(row))
            elif(linecount < 5 and linecount >0):
=======
            if linecount == 0:
                linecount += 1
                print(str(linecount) + ' : The columns')
                print(', '.join(row))
            elif linecount < 5:
>>>>>>> 09a475b0cd1c3c2f7a51f9da16b0ede4f29ade86
                linecount += 1
                print(linecount)
                print(', '.join(row))


<<<<<<< HEAD

def Main():

##    while True:
        get_muscle_data()




=======
def Main():
    get_muscle_data()
>>>>>>> 09a475b0cd1c3c2f7a51f9da16b0ede4f29ade86


if __name__ == '__main__':
    Main()
