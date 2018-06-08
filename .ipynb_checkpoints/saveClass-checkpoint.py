class savedData:
    comment = None
    def __init__(self, result, metadata, name):
        self.plot = result
        self._metadata = metadata
        self.name = name
        return
    
    @property
    def data(self):
        #Returns data as panda dataframe
        return self.plot.dframe()
    
    @property
    def state(self):
        return self._metadata
    
    def __repr__(self):
        if self.comment:
            return self.comment
        else:
            return 'No comment added'
        
    
    