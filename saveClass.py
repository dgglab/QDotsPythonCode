class savedData:
    def __init__(self, result, metadata):
        self.plot = result
        self._metadata = metadata
        return
    
    @property
    def data(self):
        #Returns data as panda dataframe
        return self.plot.dframe()
    
    @property
    def state(self):
        return self.metadata
    
    