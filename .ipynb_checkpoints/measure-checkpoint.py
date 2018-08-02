import numpy as np
from plotting import PlottingOverview
import ipywidgets as widgets
import param
import holoviews as hv
import pickle

class Measurement:
    
    _plottingManager = PlottingOverview()
    
    def __init__(self):
        self.instrumentList = {}
    
    def addInstrument(self, instrument):
        """Adds an instrument object to the experiment and ensures no overlap in name"""
        if instrument.name in self._InstrumentNamesList:
            raise Exception('Instrument name %s already exists as another Instrument or Channel name' % (instrument.name,))
            
        try:
            if instrument._multiChannel:
                for channel_name in instrument.channel_mapping:
                    if channel_name in self._InstrumentNamesList:
                        raise Exception('The channel %s already exists as another Instrument or Channel name' % (channel_name,))
                        
        except AttributeError:
            pass
        self.instrumentList[instrument.name] = instrument
        return
    
    def ramp(self, instruments, values):
        """Ramps an instrument (given by name) to a corresponding value (set by instrument driver). Input can be list of instruments and list of values"""
        values = np.array([values]).flatten()
                
        #Convert instrument names into their respective instrument objects
        instruments = self._convertInstruments(instruments)
        if len(instruments) != len(values):
            raise Exception("Different number of channels provided than voltages")
        for i in range(len(instruments)):
            instruments[i].ramp(values[i])
        return
        
    def sweep(self, sweepInst, start, end, steps, measurement):
        """1D Sweep. Input is instrument name, start and end points, number of steps, and list of measuring instrument names"""
        sweepInst = self._getInstrument(sweepInst)
        measInsts = self._convertInstruments(measurement)
        
        x_data = np.linspace(start, end, steps+1)
        points = {sweepInst.name: x_data}
        
        for inst in measInsts:
            points[inst.name] = np.full(len(x_data), np.nan)
            
        return self._plottingManager._sweep(inst1 = sweepInst, measInst = measInsts, points = points, currState = self.currentState)
        
    
    def sweep2D(self, sweepInst1, start1, end1, steps1, sweepInst2, start2, end2, steps2, measurement):
        """2D Sweep. Similar input to 1D sweep, except with second instrument"""
        sweepInst1 = self._getInstrument(sweepInst1)
        sweepInst2 = self._getInstrument(sweepInst2)
        
        measInsts = self._convertInstruments(measurement)
        
        x_data = np.linspace(start1, end1, steps1+1)
        y_data = np.linspace(start2, end2, steps2+1)
        points = {sweepInst1.name: x_data, sweepInst2.name: y_data}
        
        for inst in measInsts:
            points[inst.name] = np.full((len(y_data), len(x_data)), np.nan)
            
        return self._plottingManager._sweep(inst1 = sweepInst1, inst2= sweepInst2, measInst = measInsts, points = points, currState = self.currentState)
        
    def getPlot(self):
        """Returns plot of last finished sweep"""
        return self._plottingManager._getPlot()
        
    
    def getPlotRunning(self, wait_time =10):
        """Returns plot of currently running sweep"""
        return self._plottingManager._getPlotRunning()
    
    def abortSweep(self):
        """Aborts current sweep"""
        return self._plottingManager.abort_sweep()
    
    def abortAll(self):
        """Aborts current and all queued sweeps"""
        return self._plottingManager.abort_all()
    
    @property
    def sweepQueue(self):
        """Prints each sweep in queue and corresponding ID"""
        return self._plottingManager.current_queue
    
    def abortSweepID(self, id):
        """Aborts sweep with given ID (see sweepQueue)"""
        return self._plottingManager.abortSweepID(id)
    
    
    def _getInstrument(self, channel):
        """Returns the instrument that corresponds to a given name"""
        for name in self.instrumentList:
            instrument = self.instrumentList[name]
            try:
                if name == channel:
                    return instrument
                
                if instrument._multiChannel:
                    if instrument._nameExist(channel):
                        return instrument._getChannel(channel)
            except AttributeError:
                pass

                    

        raise Exception('No instrument with the name %s exists' % (channel,))
      
    @property
    def InstrumentNames(self):
        """Returns dictionary of all the instrument names"""
        names_dict = {}
        for name in self.instrumentList:
            instrument = self.instrumentList[name]
            if instrument._multiChannel:
                names_dict[name] = instrument.channel_mapping
            else:
                names_dict[name] = instrument
        return names_dict
    
    @property
    def _InstrumentNamesList(self):
        names = []
        for name in self.instrumentList:
            names.append(name)
            instrument = self.instrumentList[name]
            if hasattr(instrument, '_multiChannel'):
                if instrument._multiChannel:
                    names.extend(list(instrument.channel_mapping.keys()))
        return names
        
        
    
    def nameInstrument(self, currInstName, name):
        """Rename an instrument. The inputs should be current instrument name, name= 'New name'"""
        if type(name) != str:
            raise Exception("Please use a string for channel name")
        
        #Check if currInstName valid
        if currInstName not in self._InstrumentNamesList:
            raise Exception('No Instrument or Channel with name %s exists' % (currInstName))
        
        #Check if name already taken
        if name in self._InstrumentNamesList:
            raise Exception('Name already taken by %s' % (self._getInstrument(name)))
        instrument = self._getInstrument(currInstName)
        
        #Replace instrument name in instrumentList (if this is a channel of an instrument, ie QDAC, then the instrument itself handles naming)
        try:
            self.instrumentList[name] = self.instrumentList.pop(currInstName)
        except KeyError:
            pass

        instrument.name = name
        
        return
    
    def _convertInstruments(self, channels):
        """Convert list of names of instruments or channels into a list of the respective objects"""
        input_type = type(channels)
        if input_type in {np.ndarray, list, tuple}:
            if len(channels) == 1:
                return self._getInstrument(channels[0])
            return np.append(self._getInstrument(channels[0]), self._convertInstruments(channels[1:]))
        else:
            return np.array([self._getInstrument(channels)])
        
    @property
    def currentState(self):
        """Returns detailed dictionary containing all the current state information about each instrument (relies on QCoDeS snapshot feature)"""
        currState = {}
        for instrument in self.instrumentList:
            currState[instrument] = self.instrumentList[instrument].snapshot()
        return currState
    
    @property
    def readableCurrentState(self):
        """Simplified version of current state that prints easily readable state information"""
        currState = {}
        for instrument in self.instrumentList:
            self.instrumentList[instrument].print_readable_snapshot()
            print('\n')
        return
    
    
def cut(image):
    """Interactive line cuts of 2D Images"""
    
    class xy(hv.streams.Stream):
        x = param.Number(default=0.0,  doc='An X position.')
        y = param.Number(default=0.0, doc='A Y position.')
    
    x_axis = np.unique(image.dimension_values(0))
    y_axis = np.unique(image.dimension_values(1))
    xw=widgets.SelectionSlider(options=[("%g"%i,i) for i in x_axis])
    yw=widgets.SelectionSlider(options=[("%g"%i,i) for i in y_axis])
    xyst = xy(x=x_axis[0], y=y_axis[0])
    def marker(x,y):
        x_dim = {image.kdims[0].label: x}
        y_dim = {image.kdims[1].label: y}
        crosssection1 = image.sample(**x_dim).opts(norm=dict(framewise=True))#.opts(plot=dict(width = 200),norm=dict(framewise=True))
        crosssection1y = image.sample(**y_dim).opts(norm=dict(framewise=True))#.opts(plot=dict(height = 200), norm=dict(framewise=True))
        return hv.Layout(image * hv.VLine(x) * hv.HLine(y) + crosssection1+crosssection1y).cols(2)
    dmap = hv.DynamicMap(marker, streams=[xyst])
    
    def plot(x,y):
        xyst.event(x=x, y=y)
        
    hv.ipython.display(dmap)
    return widgets.interact(plot, x=widgets.SelectionSlider(options=[("%g"%i,i) for i in x_axis], continuous_update=False), y=widgets.SelectionSlider(options=[("%g"%i,i) for i in y_axis]))

def save(savedData, name = False):
    """Input is the savedData object that is returned from a sweep. Optional argument is the name of the saved file. Default behavior is to overwrite the existing file name that is automatically given"""
    if name:
        save_name = name
    else:
        save_name = savedData.name
    with open('%s.p' % (save_name,), 'wb') as file:
        pickle.dump(savedData, file)
    return

def load(filename):
    """Input is the pickled file that was automatically created from measurement or use of save function. Returns savedData object"""
    with open(filename, 'rb') as file:
        savedData = pickle.load(file)
        return savedData