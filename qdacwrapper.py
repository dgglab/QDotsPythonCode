import qdac
import numpy as np
import pandas as pd
from IPython.display import display
from gui import GUI

class qdacChannel:
    def __init__(self, qdac, number, gui, name, _qdacwrapper):
        """Class to represent individual channel of QDAC instrument. Created and 
        managed by qdacWrapper.
        
        Args:
            qdac: Actual QDAC object. This is defined in qdac.py which is
                provided by QDevil directly.
            
            number: Integer indicating which channel this corresponds to (1-48).
            
            gui: Tkinter class defined in gui.py. This handles a table that is
                displayed in a new window indicating the current status of each
                channel (name and voltage).
            
            name: Name of the channel. Used both in gui display and in
                specifiying which channel to use in Measure class
                (in measure.py).
            
            _qdacwrapper:qdacWrapper object. This is required for each channel to
                communicate back to the wrapper when voltages or names are changed. 
                Might not be necessary with better implementation of Measure class
                (in measure.py) which communicates directly to the individual
                channels.
        """
        self.qdacInst = qdac
        self.number = number
        self.guiDisplay = gui
        self._name = name
        self._qdacWrapper = _qdacwrapper
        self.voltage = 0
        loc = [number, 1]
        self.guiDisplay.update_name(loc, name)
        return
        
    def __repr__(self):
        return 'QDAC Channel %s' % (self.number,)
    
    def ramp(self, voltage):
        """Ramps this channel to the given voltage (V)
        
        Args:
            voltage: Voltage (in Volts) to ramp to
        """
        #Uncomment below when actually connected to qdac
        #self.qdacInst.setDCVoltage(channel = number, volts = voltage)
        self.voltage = voltage
        self._qdacWrapper.voltage_dict[self.number] = voltage
        
        #Location of gui is (channel #, 2) -- 2 is for column of voltages
        self.display_voltage([self.number, 2], voltage)
        
    def display_voltage(self, loc, value):
        """Sends a value to be displayed by associated Tkinter gui.
        Don't actually need loc input since it is static for a given channel,
        but keeping for now depending on how this changes.
        
        Args:
            loc: location as a size 2 iterable that points to the associated
                entry for this channel's voltage reading in the Tkinter gui
                (see gui.py)
                
            value: Value to display. Should usually just be the voltage output
        """
        self.guiDisplay.submit_to_tkinter(loc, np.round(value,6))
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, name):
        self._qdacWrapper.channel_mapping[name] = self._qdacWrapper.channel_mapping.pop(self.name)
        self._name = name
        loc = [self.number, 1]
        self.guiDisplay.update_name(loc, name)
    
class qdacWrapper:
    """Wrapper class for QDevil QDAC. Manages each individual channel through a
    dictionary. Important aspects are the _multiChannel property and snapshot
    method. Most of the other methods are now redundant by the way the Measure
    class works and I should remove."""
    location = '/dev/ttyUSB0'
    qdacInst= 1
    name = 'qdac'
    _multiChannel = True
    
    
    def __init__(self):
        
        self.guiDisplay = GUI()
        self.guiDisplay.start()
        
        self.channel_mapping = {'qdac%s' % (n,):qdacChannel(qdac = self.qdacInst, number = n, gui = self.guiDisplay, name= 'qdac%s' % (n,), _qdacwrapper = self) for n in range(1,49)}
        self.voltage_dict = {n: 0 for n in range(1,49)}
        
        return
    
    def _nameGate(self, name, channel):
        if type(name) != str:
            raise Exception("Please use a string for channel name")
        
        if type(channel) != int or not (1 <= channel <= 48):
            raise Exception("Please use an integer 1-48 for channel number")
        
        
        chan_name = self._getName(channel)
        print("Overriding %s = Channel %s to %s = Channel %s" % (chan_name, channel, name, channel))
        
        self.channel_mapping[name] = self.channel_mapping.pop(chan_name) #Deletes old entry for name that corresponded to given channel
        self.channel_mapping[name]._name = name
        
        #Send updated name to GUI
        number = self.channel_mapping[name].number
        #Location is (number, 1) -- 1 is for the column of names
        loc = [number, 1]
        self.guiDisplay.update_name(loc, name)
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
        
    def _getChannel(self, name):
        if self._nameExist(name):
            return self.channel_mapping[name]
        
        else:
            raise Exception("No channel with the name %s exists!" % (name,))
            
    def _getName(self, channel):
        for name in self.channel_mapping:
            if self.channel_mapping[name].number == channel:
                return name
    
    def _nameExist(self, name):
        if type(name) != str:
            raise Exception("Input %s is not a string!" % (name,))
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
        
    def snapshot(self):
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
    
    def print_readable_snapshot(self):
        print(self.name + ':\n')
        display(self.snapshot())
            
        
            
    

