from pymeasure.instruments import Mock
import numpy as np

class InstrumentWrapper:
    x  = 0
    
    
class MockWrapper(Mock):
    #_defName = 'mock'
    
    def __init__(self, name = 'mock'):
        super().__init__()
        self._name = name
        self._multiChannel = False
        self.output_voltage  = 0
        
    def ramp(self, volt):
        self.output_voltage = volt
        
        
class MockMeasure:
    def __init__(self, name = 'measure'):
        self._name = name
        self._multiChannel = False
    
    def measure(self):
        return np.random.randn(1)[0]