import csv

def get_muscle_data():
    ''' it opens the csv file and sends the data to the client.'''
    with open('0.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        linecount = 0
        for row in filereader:
            if(linecount == 0):
                linecount += 1
                print(str(linecount)+ ' : The columns')
                print(', '.join(row))
            elif(linecount < 5 and linecount >0):
                linecount += 1
                print(linecount)
                print(', '.join(row))



def Main():

##    while True:
        get_muscle_data()






if __name__ == '__main__':
    Main()
