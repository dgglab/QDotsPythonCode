import numpy as np
from plotting import PlottingOverview
import ipywidgets as widgets
import param
import holoviews as hv
import pickle

class Measurement:
    """Overview object that manages all instruments in experiment and handles measurements. All basic commands (such as ramping, sweeping, renaming of instruments) should be run through this object directly."""
    
    def __init__(self):
        self.instrumentDict = {}
        self._plottingManager = PlottingOverview()
    
    def ramp(self, instruments, values):
        """Ramps an instrument (given by name) to a corresponding value (set by instrument driver).
            
        Args:
            instruments: Name given to instrument. Can be an array of names.
            
            values: Value to ramp corresponding instrument to. Can also be an array of values that match length of instruments"""
        if self._plottingManager.currentlyRunning:
            raise Exception("Sweep currently in progress. Please wait for sweeps to finish before ramping instruments.")
        values = np.array([values]).flatten()
                
        #Convert instrument names into their respective instrument objects
        instruments = self._convertInstruments(instruments)
        if len(instruments) != len(values):
            raise Exception("Different number of channels provided than voltages")
        
        for inst, value in zip(instruments, values):
            inst.ramp(value)
        return
        
    def sweep(self, sweepInst, start, end, steps, measureParams):
        """1D Sweep. Will display plot inline, but if assigned (ie result = sweep(..)) the return value should also be the updating plot.
        
        Args:
            sweepInst: Name of instrument to be swept
            
            start: Initial value to sweep from
            
            end: Final value to sweep to
            
            steps: Number of steps between start and end value. One additional step is automatically added for convenience, 
                such as a sweep from 2 to 5 in 3 steps actually has 4 steps (2,3,4,5).
                
            measureParams: List of names of measurement instruments to be measured at each point.
        """
        
        sweepInst = self._getInstrument(sweepInst)
        measInsts = self._convertInstruments(measureParams)
        
        x_data = np.linspace(start, end, steps+1)
        points = {sweepInst.name: x_data}
        
        for inst in measInsts:
            points[inst.name] = np.full(len(x_data), np.nan)
            
        return self._plottingManager._sweep(sweepInst, measInsts, points, self.currentState)
        
    
    def sweep2D(self, sweepInst1, start1, end1, steps1, sweepInst2, start2, end2, steps2, measureParams):
        """2D Sweep. Will display plot inline, but if assigned (ie result = sweep(..)) the return value should also be the updating plot.
        
        Args:
            sweepInst1: Name of first instrument to be swept. This will be slow axis.
            
            start1: Initial value to sweep from for first instrument
            
            end1: Final value to sweep to for first instrument.
            
            steps1: Number of steps between start and end value for first instrument. One step added (see 'sweep' docstring)
            
            sweepInst2: Name of second instrument to be swept. This will be fast axis.
            
            start2: Initial value to sweep from for second instrument
            
            end2: Final value to sweep to for second instrument.
            
            steps2: Number of steps between start and end value for second instrument. One step added (see 'sweep' docstring)
            
            measureParams: List of names of measurement instruments to be measured at each point.
        """
        sweepInst1 = self._getInstrument(sweepInst1)
        sweepInst2 = self._getInstrument(sweepInst2)
        measInsts = self._convertInstruments(measureParams)
        
        x_data = np.linspace(start1, end1, steps1+1)
        y_data = np.linspace(start2, end2, steps2+1)
        points = {sweepInst1.name: x_data, sweepInst2.name: y_data}
        
        for inst in measInsts:
            points[inst.name] = np.full((len(y_data), len(x_data)), np.nan)
            
        return self._plottingManager._sweep(sweepInst1, measInsts, points, self.currentState, sweepInst2)
        
    def getPlot(self):
        """Returns savedData object created by last finished sweep"""
        return self._plottingManager._getPlot()
        
    
    def getPlotRunning(self, wait_time=10):
        """Returns savedData object of currently running sweep
        
        Args:
            wait_time: (default=10) This is how long (in seconds) function will wait until currently running thread places the plot in the queue. This argument should only be relevant if at a given point the system waits longer than 10 seconds to measure.
        """
        return self._plottingManager._getPlotRunning(wait_time)
    
    def abortSweep(self):
        """Aborts current sweep"""
        self._plottingManager.abort_sweep()
    
    def abortAll(self):
        """Aborts current and all queued sweeps"""
        self._plottingManager.abort_all()
    
    @property
    def sweepQueue(self):
        """Prints each sweep in queue and corresponding ID"""
        self._plottingManager.current_queue
    
    def abortSweepID(self, ID):
        """Aborts sweep with given ID
        
        Args:
            ID: ID number to abort. This can be found by sweepQueue property.
        """
        self._plottingManager.abortSweepID(ID)
    
    
    def _getInstrument(self, instName):
        """Returns the instrument object that corresponds to a given name.
        
        Args:
            instName: Name of instrument
        """
        for name in self.instrumentDict:
            instrument = self.instrumentDict[name]
            try:
                if name == instName:
                    return instrument
                
                if instrument._multiChannel:
                    if instrument._nameExist(instName):
                        return instrument._getChannel(instName)
            except AttributeError:
                pass
        raise Exception('No instrument with the name %s exists' % (channel,))
      
    @property
    def InstrumentNames(self):
        """Returns dictionary of all the instrument names (including individual channels of multi-channeled instruments). The format is {name: instrument}"""
        names_dict = {}
        for name in self.instrumentDict:
            instrument = self.instrumentDict[name]
            if instrument._multiChannel:
                names_dict[name] = instrument.channel_mapping
            else:
                names_dict[name] = instrument
        return names_dict
    
    @property
    def _InstrumentNamesList(self):
        """Returns a flattened out list of all instrument names including individual channels"""
        names = []
        for name in self.instrumentDict:
            names.append(name)
            instrument = self.instrumentDict[name]
            if hasattr(instrument, '_multiChannel'):
                if instrument._multiChannel:
                    names.extend(list(instrument.channel_mapping.keys()))
        return names
        
    def addInstrument(self, instrument):
        """Adds an instrument to the experiment and ensures no overlap in name.
        
        Args:
            instrument: Instrument object
        """
        if instrument.name in self._InstrumentNamesList:
            raise Exception('Instrument name %s already exists as another Instrument or Channel name' % (instrument.name,))
            
        try:
            if instrument._multiChannel:
                for channel_name in instrument.channel_mapping:
                    if channel_name in self._InstrumentNamesList:
                        raise Exception('The channel %s already exists as another Instrument or Channel name' % (channel_name,))
                        
        except AttributeError:
            pass
        self.instrumentDict[instrument.name] = instrument
    
    def nameInstrument(self, currInstName, name):
        """Rename an instrument. Will raise an error if the new name is already being used.
        
        Args:
            currInstName: The current name of the instrument to be renamed.
            
            name: New name of the instrument
        """
        if self._plottingManager.currentlyRunning:
            raise Exception("Sweep currently in progress. Please wait for sweeps to finish before renaming instruments.")
        
        if type(name) != str:
            raise Exception("Please use a string for channel name")
        
        #Check if currInstName valid
        if currInstName not in self._InstrumentNamesList:
            raise Exception('No Instrument or Channel with name %s exists' % (currInstName))
        
        #Check if name already taken
        if name in self._InstrumentNamesList:
            raise Exception('Name already taken by %s' % (self._getInstrument(name)))
        instrument = self._getInstrument(currInstName)
        
        #Replace instrument name in instrumentDict (if this is a channel of an instrument, ie QDAC, then the instrument itself handles naming)
        try:
            self.instrumentDict[name] = self.instrumentDict.pop(currInstName)
        except KeyError:
            pass

        instrument.name = name
    
    def _convertInstruments(self, channels):
        """Convert list of names of instruments or channels into a list of the respective instrument objects. Returns this list of instrument objects"""
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
        for instrument in self.instrumentDict:
            currState[instrument] = self.instrumentDict[instrument].snapshot()
        return currState
    
    @property
    def readableCurrentState(self):
        """Prints a simplified version of current state that prints easily readable state information"""
        currState = {}
        for instrument in self.instrumentDict:
            self.instrumentDict[instrument].print_readable_snapshot()
            print('\n')
        return
    
    
def cut(image):
    """Interactive line cuts of 2D Images. Uses ipywidgets for interactivity.
    
    Args:
        image: Image to take line cuts of. The type should be a Holoviews Image.
    """
    
    #Defines a Holoviews Stream class for an x,y position
    class xy(hv.streams.Stream):
        x = param.Number(default=0.0,  doc='An X position.')
        y = param.Number(default=0.0, doc='A Y position.')
    
    #Points for each axis
    x_axis = np.unique(image.dimension_values(0))
    y_axis = np.unique(image.dimension_values(1))
    
    #Create a slider widget to control x and y cut locations
    xw=widgets.SelectionSlider(options=[("%g"%i,i) for i in x_axis])
    yw=widgets.SelectionSlider(options=[("%g"%i,i) for i in y_axis])
    
    xyst = xy(x=x_axis[0], y=y_axis[0])
    
    #Define function that creates Holoviews Layout. This Layout contains the original 2D image, lines going through the x,y point specified, and the line cuts themselves
    def marker(x,y):
        x_dim = {image.kdims[0].label: x}
        y_dim = {image.kdims[1].label: y}
        crosssection1 = image.sample(**x_dim).opts(norm=dict(framewise=True))
        crosssection1y = image.sample(**y_dim).opts(norm=dict(framewise=True))
        return hv.Layout(image * hv.VLine(x) * hv.HLine(y) + crosssection1+crosssection1y).cols(2)
    
    #Create DynamicMap of above Layout such that the x,y positions can be streamed and updated
    dmap = hv.DynamicMap(marker, streams=[xyst])
    
    #Function that widget can call to update DynamicMap. When this Stream object updates the x,y position via the Slider widget and then the event method called, the DynamicMap recomputes marker based off this and thus updates the line cut.
    def plot(x,y):
        xyst.event(x=x, y=y)
        
    hv.ipython.display(dmap)
    
    #Return statement is the syntax for interacting widgets (see ipywidget docs). 
    return widgets.interact(plot, x=widgets.SelectionSlider(options=[("%g"%i,i) for i in x_axis], continuous_update=False), y=widgets.SelectionSlider(options=[("%g"%i,i) for i in y_axis]))

def save(savedData, name = False):
    """Saves data into pickle format in the current folder.
    
    Args:
        savedData: The data to be saved. This should be a savedData object.
        
        name: (Optional) Name to save the file as. The default behavior is to use the name provided by the savedData object, which is the data and time the object was created. This means that it overwrites the file that was autosaved when a sweep was run.
    """
    if name:
        save_name = name
    else:
        save_name = savedData.name
    with open('%s.p' % (save_name,), 'wb') as file:
        pickle.dump(savedData, file)

def load(filename):
    """Loads a pickle file and returns the associated savedData object
    
    Args:
        filename: Name of the pickle file to load
    """
    with open(filename, 'rb') as file:
        savedData = pickle.load(file)
        return savedData