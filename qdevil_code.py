import qdac
import numpy as np
import pandas as pd

class qdacChannel:
    voltage = 0
    def __init__(self, qdac, number):
        self.qdacInst = qdac
        self.number = number
    
    def __repr__(self):
        return 'QDAC Channel %s' % (number,)
    
    def ramp(self, voltage):
        self.qdacInst.setDCVoltage(channel = number, volts = voltage)
        self.voltage = voltage

class qdacWrapper:
    location = '/dev/ttyUSB0'
    qdacInst= 1
    _name = 'qdac'
    channel_mapping = {'qdac%s' % (n,):qdacChannel(qdacInst, number) for n in range(1,49)}
    #_defaultMapping = {'qdac%s' % (n,):qdacChannel(qdacInst, number) for n in range(1,49)}
    #voltage_list = np.zeros(48)
    
    voltage_dict = {n: 0 for n in range(1,49)}
    
    
    def _nameGate(self, name, channel):
        if type(name) != str:
            raise Exception("Please use a string for channel name")
        
        if type(channel) != int or not (1 <= channel <= 48):
            raise Exception("Please use an integer 1-48 for channel number")
        
        
        chan_name = self._getName(channel)
        print("Overriding %s = Channel %s to %s = Channel %s" % (chan_name, channel, name, channel))
        
        self.channel_mapping[name] = self.channel_mapping.pop(chan_name) #Deletes old entry for name that corresponded to given channel
        return
        
        
    def _ramp(self, channels, voltages):
        """Ramp selected channels to the given voltages. Input can be the Name or number of the channel and can also be given as an array"""
        #Name can be the name given to the channel or the actual channel number itself
        if type(channels) in {np.ndarray, list, tuple}:
            if len(channels) != len(list(voltages)):
                raise Exception("Different number of channels provided than voltages")
        channels_list = self._convertChannels(channels) #Turns all channels input into array of integers that can be passed to QDAC
        #with qdac.qdac(self.location) as q:
        for i in range(len(channels_list)):
            qdacInst.setDCVoltage(channel=channels_list[i], volts = voltages[i])
            #self.voltage_list[channels_list[i]-1] = voltages[i]
            self.voltage_dict[channels_list[i]] = voltages[i]
        return
        
        
        
    def sweep(self):
        return
    
    def sweep2D(self):
        return
    
    
    def _getChannel(self, name):
        if self._nameExist(name):
            return self.channel_mapping[name]
        
        else:
            raise Exception("No channel with the name %s exists!" % (name,))
            
    def _getName(self, channel):
        if self._channelExist(channel):
            for _name, _channel in self.channel_mapping.items():
                if _channel == channel.number:
                    return _name
        else:
            raise Exception("Channel %s has not been assigned a name!" % (channel,))
    
    def _nameExist(self, name):
        if type(name) != str:
            raise Exception("Input %s is not a string!" % (name,))
        #if name in self.channel_mapping.keys():
        #    return True
        #else:
        #    return False
        return (name in self.channel_mapping.keys())
    
    def _channelExist(self,channel):
        if type(channel) != int:
            raise Exception("Input %s is not an integer!" % (channel,))
        return channel in self.channel_mapping.values()
    
    def _convertChannels(self, channels):
        """Convert list of channels (given by name or number) into list of numbers"""
        if len(channels) ==1:
            channels = channels[0]
        input_type = type(channels)
        if input_type in {np.ndarray, list, tuple}:
            return np.append(self._parseChannel(channels[0]), self._convertChannels(channels[1:]))
        else:
            return self._parseChannel(channels)
    
    def _parseChannel(self, channel):
        """Parses input such that it returns the channel number given either name or number."""
        input_type = type(channel)
        if input_type == str:
            return np.array([self._getChannel(channel)])
        elif input_type == int and 1 <= channel <= 48:
            return np.array([channel])
        else:
            raise Exception("Inputs should an existing Channel name or integer between 1 and 48")
        
    def _convertDF(self):
        #Convert voltage table to pandas data frame
        #channel_table = {'Channel Number': [], 'Channel Name': [], 'Voltage': []}
        channel_table = {'Channel Name': [], 'Voltage': []}
        channel_index = []
        for i in range(1,49):
            
            #channel_table['Channel Number'].append(i)
            channel_index.append('Channel %s' % (i,))
            channel_table['Voltage'].append(self.voltage_dict[i])
            try:
                channel_table['Channel Name'].append(self._getName(i))
            except:
                channel_table['Channel Name'].append('')

        channel_df = pd.DataFrame(data=channel_table, index = channel_index)
        #channel_df = channel_df[['Channel Number', 'Channel Name', 'Voltage']]
        
        #Rearrange columns to ensure that Channel name comes before Voltage
        channel_df = channel_df[['Channel Name', 'Voltage']]
        return channel_df
            
        
            
    
    
class Measurements:
    #qdevil= QDevil()
    instrumentList = {}
    voltage_list = np.zeros(48)
    
    def add_instrument(self, instrument):
        self.inst = instrument #obviously not correct, will need to correctly handle different instruments and how to call
        self.instrumentList[instrument._name] = instrument
            
        #Check names of every instrument so that there is no overlap
        
    def _parseInstrument(self, input_channel):
        return
    
    def ramp(self, channels, values):
        instrument = self._getInstrument(channel)
        instrument.ramp(value)
        return
        
        
    def sweep(self):
        return
    
    def sweep2D(self, chan1, start1, end1, steps1, chan2, start2, end2, steps2):
        inst1 = self._getInstrument(chan1)
        inst2 = self._getInstrument(chan2)
        
        
        return
    
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
