from pymeasure.instruments import Mock

class InstrumentWrapper:
    x  = 0
    
    
class MockWrapper(Mock):
    #_defName = 'mock'
    
    def __init__(self, name = 'mock'):
        super().__init__()
        self._name = name
        self._multiChannel = False
        
    def ramp(self, volt):
        self.output_voltage = volt
        
        