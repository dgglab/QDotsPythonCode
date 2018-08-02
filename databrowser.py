import pickle
import pandas as pd
import glob
import os.path
from IPython.display import Image, HTML 

def listData():
    """Lists all the saved data files in a table with description, date, and thumbnail"""
    
    
    #Prevent truncation of long strings. Also necessary for images which have long file names, especially including HTML formatting
    pd.set_option('display.max_colwidth', -1)
        
    data_table = _dataTable()
    #Create dataframe based off dictionary, and rearrange columns 
    data_df = pd.DataFrame(data = data_table)
    data_df = data_df[['Date', 'Description', 'Comment', 'Thumbnail']]
    
    #HTML function renders the literal text in each column as HTML
    return HTML(data_df.to_html(escape=False))


def _load(filename):
    """Input is the pickled file that was automatically created from measurement or use of save function. Returns savedData object"""
    with open(filename, 'rb') as file:
        savedData = pickle.load(file)
        return savedData
    
def loadnum(number):
    """Load filename by index of given by listData"""
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

def query(comment):
    """Returns table of all data that contains the input comment"""
    pd.set_option('display.max_colwidth', -1)
    
    data_table = _dataTable()
    
    data_df = pd.DataFrame(data = data_table)
    data_df = data_df[['Date', 'Description', 'Comment', 'Thumbnail']]
    data_df_queried = data_df.loc[data_df.loc[:,'Comment'].str.contains(comment)]
    return HTML(data_df_queried.to_html(escape=False))

def _dataTable():
    #Get all files with .p extension
    datafiles = glob.glob('*.p')
    
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
                #If a picture exists, add as thumbnail using HTML formatting
                data_table['Thumbnail'].append('<img src="%s" height="50" width="50"/>' % (thumbnail_file,))
            else:
                data_table['Thumbnail'].append('')
                
        except EOFError:
            pass
        
    return data_table
    

