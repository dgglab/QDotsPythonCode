import holoviews as hv
import numpy as np
from IPython.display import display

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
    def prettyState(self):
        for inst in self._metadata:
            snapshot = self._metadata[inst]
            if type(snapshot) == dict:
                self._print_readable_snapshot(snapshot)
            else:
                print(inst + ':\n')
                display(snapshot)
            print('\n')
        return
    
    @property
    def plot(self):
        if type(self._plot) == hv.Image:
            return self._plot.opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
        return self._plot
    
    def __repr__(self):
        if self.comment:
            return self.comment
        else:
            return self.description
        
    def _print_readable_snapshot(self, snapshot, update: bool=False,
                                    max_chars: int=80) -> None:
            """
            Prints a readable version of the snapshot.
            The readable snapshot includes the name, value and unit of each
            parameter.
            A convenience function to quickly get an overview of the
            status of an instrument.
            Args:
                update: If True, update the state by querying the
                    instrument. If False, just use the latest values in memory.
                    This argument gets passed to the snapshot function.
                max_chars: the maximum number of characters per line. The
                    readable snapshot will be cropped if this value is exceeded.
                    Defaults to 80 to be consistent with default terminal width.
            """
            floating_types = (float, np.integer, np.floating)
            #snapshot = self.snapshot(update=update)

            par_lengths = [len(p) for p in snapshot['parameters']]

            # Min of 50 is to prevent a super long parameter name to break this
            # function
            par_field_len = min(max(par_lengths)+1, 50)

            print(snapshot['parameters']['IDN']['instrument_name'] + ':')
            print('{0:<{1}}'.format('\tparameter ', par_field_len) + 'value')
            print('-'*max_chars)
            for par in sorted(snapshot['parameters']):
                name = snapshot['parameters'][par]['name']
                msg = '{0:<{1}}:'.format(name, par_field_len)

                # in case of e.g. ArrayParameters, that usually have
                # snapshot_value == False, the parameter may not have
                # a value in the snapshot
                val = snapshot['parameters'][par].get('value', 'Not available')

                unit = snapshot['parameters'][par].get('unit', None)
                if unit is None:
                    # this may be a multi parameter
                    unit = snapshot['parameters'][par].get('units', None)
                if isinstance(val, floating_types):
                    msg += '\t{:.5g} '.format(val)
                else:
                    msg += '\t{} '.format(val)
                if unit is not '':  # corresponds to no unit
                    msg += '({})'.format(unit)
                # Truncate the message if it is longer than max length
                if len(msg) > max_chars and not max_chars == -1:
                    msg = msg[0:max_chars-3] + '...'
                print(msg)

            for submodule in snapshot['submodules'].values():
                print_readable_snapshot(submodule)
                #if hasattr(submodule, '_channels'):
                #    submodule = cast('ChannelList', submodule)
                #    if submodule._snapshotable:
                #        for channel in submodule._channels:
                #            channel.print_readable_snapshot()
                #else:
                #    submodule.print_readable_snapshot(update, max_chars)
