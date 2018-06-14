class savedData:
    def __init__(self, result, metadata, name, description):
        self._plot = result
        self._metadata = metadata
        self.name = name
        
        #This assumes that object always created with the date as the name (which is the current functionality)
        self.date = name
        
        self.description = description
        self.comment = None
        return
    
    @property
    def data(self):
        #Returns data as panda dataframe
        return self.plot.dframe()
    
    @property
    def state(self):
        return self._metadata
    
    @property
    def plot(self):
        return self._plot.opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
    
    def __repr__(self):
        if self.comment:
            return self.comment
        else:
            return self.description
        
    
    