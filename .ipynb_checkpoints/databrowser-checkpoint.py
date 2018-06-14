import pickle
import pandas as pd
import glob
import os.path
from IPython.display import Image, HTML 

def list_data():
    #Prevent truncation of long strings. Also necessary for images which have long file names
    pd.set_option('display.max_colwidth', -1)
    
    datafiles = glob.glob('*.p')
    print(datafiles)
    data_table = {'Date': [], 'Description': [], 'Comment': [], 'Thumbnail': []}
    for file in datafiles:
        try:
            data = _load(file)
            data_table['Date'].append(data.date)
            data_table['Description'].append(data.description)
            if data.comment:
                data_table['Comment'].append(data.comment)
            else:
                data_table['Comment'].append('')
            
            thumbnail_file = './DataThumbnails/' +file[:-1] +'png' 
            if os.path.isfile(thumbnail_file):
                data_table['Thumbnail'].append('<img src="%s"/>' % (thumbnail_file,))
            else:
                data_table['Thumbnail'].append('')
                
        except EOFError:
            pass
    print(data_table['Thumbnail'])
    data_df = pd.DataFrame(data = data_table)
    data_df = data_df[['Date', 'Description', 'Comment', 'Thumbnail']]
    return HTML(data_df.to_html(escape=False))


def _load(filename):
    """Input is the pickled file that was automatically created from measurement or use of save function. Returns savedData object"""
    with open(filename, 'rb') as file:
        savedData = pickle.load(file)
        return savedData
    
def loadnum(number):
    """Load filename by index of Pandas Dataframe given by list_data"""
    datafiles = glob.glob('*.p')
    data_table = {'Date': [], 'Description': [], 'Comment': []}
    i = 0
    for file in datafiles:
        try:
            data = _load(file)
            if i == number:
                return data
            i += 1
        except EOFError:
            pass
    return 'Index out of range!'
    

