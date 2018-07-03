import numpy as np
from plotting import PlottingOverview

class Measurement:
    instrumentList = {}
    _plottingManager = PlottingOverview()
    
    def addInstrument(self, instrument):
        if instrument._name in self._InstrumentNamesList:
            raise Exception('Instrument name %s already exists as another Instrument or Channel name' % (instrument._name,))
            
        try:
            if instrument._multiChannel:
                for channel_name in instrument.channel_mapping:
                    if channel_name in self._InstrumentNamesList:
                        raise Exception('The channel %s already exists as another Instrument or Channel name' % (channel_name,))
                        
        except AttributeError:
            pass
        self.instrumentList[instrument._name] = instrument
            
        
    def _parseInstrument(self, input_channel):
        return
    
    def ramp(self, instruments, values):
        if type(instruments) in {np.ndarray, list, tuple}:
            if len(instruments) != len(list(voltages)):
                raise Exception("Different number of channels provided than voltages")
                
        #convert instrument names into their respective instrument objects
        instruments = self._convertInstruments(instruments)
        for i in range(len(instruments)):
            instruments[i].ramp(values[i])
        
        
    def sweep(self, inst, start, end, steps, measurement):
        inst = self._getInstrument(inst)
        measInst = self._getInstrument(measurement)
        
        x_data = np.linspace(start, end, steps+1)
        points = {inst._name: x_data, measInst._name:np.full(len(x_data), np.nan)}
        return self._plottingManager._sweep(inst1 = inst, measInst = measInst, points = points)
        
    
    def sweep2D(self, inst1, start1, end1, steps1, inst2, start2, end2, steps2, measurement):
        inst1 = self._getInstrument(inst1)
        inst2 = self._getInstrument(inst2)
        measInst = self._getInstrument(measurement)
        
        x_data = np.linspace(start1, end1, steps1+1)
        y_data = np.linspace(start2, end2, steps2+1)
        points = {inst1._name: x_data, inst2._name: y_data, measInst._name:np.full((len(y_data),len(x_data)), np.nan)}
        return self._plottingManager._sweep(inst1, inst2= inst2, measInst = measInst,points = points)
        
    
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
                    names.append(instrument.channel_mapping.keys())
        return names
        
        
    
    def nameInstrument(self, instrument, name, channel = False):
        """Rename an instrument. The inputs should be instrument, name= 'New name', channel = channel number"""
        #instrument = self._getInstrument(instrument_name)
        #instrument = instrumentList[instrument_name]
        #if instrument._multiChannel:
            #if not channel:
                #raise Exception('Instrument contains multiple channels, please provide a channel number as defined in that instrument class')
            #else:
                #instrument._nameGate(name, channel, override = True)
                
        #else:
            #instrument._name = name
        
        #Check if name alreday taken
        if name in self._InstrumentNamesList:
            raise Exception('Name already taken by %s' % (self._getInstrument(name)))
        
        try:
            if instrument._multiChannel:
                if not channel:
                    raise Exception('Instrument contains multiple channels, please provide a channel number as defined in that instrument class')
                instrument._nameGate(name, channel)
                return
        except AttributeError:
            pass
        instrumentList[name] = instrument
        instrument._name = name
        
        return
    
    def _convertInstruments(self, channels):
        """Convert list of names of instruments or channels into a list of the respective objects"""
        input_type = type(channels)
        if input_type in {np.ndarray, list, tuple}:
            if channels.size == 1:
                return self._getInstrument(channels[0])
            return np.append(self._getInstrument(channels[0]), self._convertInstruments(channels[1:]))
        else:
            return np.array([self._getInstrument(channels)])
        
    def currentState(self):
        for instrument in instrumentList.values():
            pass
        return