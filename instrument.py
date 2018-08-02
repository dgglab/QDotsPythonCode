from qcodes.tests.instrument_mocks import DummyInstrument
import numpy as np

class MockWrapper(DummyInstrument):
    #_defName = 'mock'
    
    def __init__(self, name = 'mock', gates =['ch1']):
        super().__init__(name, gates)
        #self._name = name
        self._multiChannel = False
        self.gates = gates
        
    def ramp(self, volt):
        self.set(self.gates[0], volt)
        
        
class MockMeasure(DummyInstrument):
    def __init__(self, name = 'measure', gates=['voltage']):
        super().__init__(name, gates)
        #self._name = name
        self._multiChannel = False
        self.gates = gates
    
    def measure(self):
        return np.random.randn(1)[0]+self.get(self.gates[0])