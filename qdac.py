# qdac.py
# Copyright QDevil ApS, March 2018

import serial
import time

class Waveform:
    # Enum-like class defining the built-in waveform types
    sine = 1
    square = 2
    triangle = 3
    all = [sine, square, triangle]

class Generator:
    # Enum-like class defining the waveform generators
    DC = 0
    generator1 = 1
    generator2 = 2
    generator3 = 3
    generator4 = 4
    generator5 = 5
    generator6 = 6
    generator7 = 7
    generator8 = 8
    AWG = 9
    pulsetrain = 10
    functionGenerators = [generator1, generator2, generator3, generator4, generator5, generator6,
           generator7, generator8]
    syncGenerators = functionGenerators + [AWG, pulsetrain]
    all = [DC] + syncGenerators

class qdac():
    # Main QDAC instance class
    channelNumbers = range(1,49)
    noChannel = 0
    syncChannels = [1, 2, 3, 4, 5]

    def __init__(self, port, verbose=False):
        # Constructor
        # port: Serial port for QDAC
        # verbose: Print serial communication during operation. Useful for debugging
        self.port = port
        self.verbose = verbose
        self.voltageRange = {ch: 10.0 for ch in qdac.channelNumbers} # Assumes that QDAC has power-on values
        self.currentRange = {ch: 100e-6 for ch in qdac.channelNumbers} # Assumes that QDAC has power-on values

    def __enter__(self):
        self.sport = serial.Serial(port=self.port, baudrate=460800, bytesize=serial.EIGHTBITS,
                                   parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=0.5)
        return self

    def __exit__(self, type, value, traceback):
        self.sport.close()

    def setVoltageRange(self, channel, range):
        # Set the voltage output range of a QDAC channel
        # range must be 1.0 or 10.0 (unit is V)
        self._validateChannel(channel)
        if range == 10.0:
            rangeFlag = 0
        elif range == 1.0:
            rangeFlag = 1
        else:
            raise Exception("Invalid voltage range %d" % range)
        self.voltageRange[channel] = range
        self._sendReceive("vol %d %d" % (channel, range))

    def setCurrentRange(self, channel, range):
        # Set the current sensing range of a QDAC channel
        # range must be 1e-6 or 100e-6 (unit is A)
        self._validateChannel(channel)
        if range == 1e-6:
            rangeFlag = 0
        elif range == 100e-6:
            rangeFlag = 1
        else:
            raise Exception("Invalid current range %d" % range)
        self.currentRange[channel] = range
        self._sendReceive("cur %d %d" % (channel, range))

    def setDCVoltage(self, channel, volts):
        # Set the immediate DC voltage of a QDAC channel
        # This only works if setChannelOutput has been set to Generator.DC, which is the power-on setting!!
        self._validateChannel(channel)
        self._validateVoltage(channel, volts)
        self._sendReceive("set %d %f" % (channel, volts))

    def setCalibrationChannel(self, channel):
        # Connect a QDAC channel to the Calibration output. Useful for testing the output performance
        # Set channel to 0 to disconnect all channels from the Calibration output
        if channel != qdac.noChannel:
            self._validateChannel(channel)
        self._sendReceive("cal %d" % channel)

    def readTemperature(self, board, position):
        # Read the temperature in Celsius inside the QDAC at different positions
        # Board: 0-5
        # Channel: 0-2
        # board 0 is channel 1-8, board 1 is channel 9-16, etc.
        if board not in [0,1,2,3,4,5] or position not in [0,1,2]:
            raise Exception("readTemperature: Invalid board %d or position %d" % (board, position))
        reply = self._sendReceive("tem %d %d" % (board, position))
        return float(reply.split(":", 1)[1])

    def defineFunctionGenerator(self, generator, waveform, period, dutycycle=0, repetitions=-1):
        # Define a function generator
        # generator: Generator.generator1, ..., Generator.generator8
        # waveform: Waveform.sine, Waveform.square, Waveform.triangle
        # period: Number of samples in waveform period
        # dutycycle: 0-100, used for square and triangle waveforms to define shape
        # repetitions: How many times the waveform is repeated. -1 means infinite
        # Note: The amplitude is always max. range of the channel. Set the amplitude in setChannelOutput
        if generator not in Generator.functionGenerators:
            raise Exception("Invalid generator number (must be 1-8): %d" % generator)
        if waveform not in Waveform.all:
            raise Exception("Invalid waveform: %d" % waveform)
        if period < 1:
            raise Exception("Invalid waveform period: %d" % period)
        if repetitions < -1 or repetitions > 0x7FFFFFFF:
            raise Exception("Invalid number of repetitions: %d" % repetitions)
        if dutycycle < 0 or dutycycle > 100:
            raise Exception("Invalid dutycycle: %d" % dutycycle)
        self._sendReceive("fun %d %d %d %d %d" % (generator, waveform, period, dutycycle, repetitions))

    def definePulsetrain(self, lowDuration, highDuration, lowVolts, highVolts, repetitions=-1):
        # Define a pulse train function generator
        # The generator is always Generator.pulsetrain
        # lowDuration, highDuration, lowVolts, highVolts defines the pulsetrain
        # repetitions: How many times the waveform is repeated. -1 means infinite
        if lowDuration < 0 or lowDuration > 0x7FFFFFFF:
            raise Exception("Invalid lowDuration: %d" % lowDuration)
        if highDuration < 0 or highDuration > 0x7FFFFFFF:
            raise Exception("Invalid highDuration: %d" % highDuration)
        if lowVolts < -10.0 or lowVolts > 10.0:
            raise Exception("Invalid lowVolts: %f" % lowVolts)
        if highVolts < -10.0 or highVolts > 10.0:
            raise Exception("Invalid highVolts: %f" % highVolts)
        if repetitions < -1 or repetitions > 0xFFFFFFFF:
            raise Exception("Invalid number of repetitions: %d" % repetitions)
        self._sendReceive("pul %d %d %f %f %d" % (lowDuration, highDuration, lowVolts, highVolts, repetitions))

    def defineAWGraw(self, samples, repetitions=-1): # Sample rate is 1kS/s
        # Define a pulse train function generator
        # The generator is always Generator.AWG
        # samples: An array of volt, defines the pulsetrain samples at 1000 samples per second. Max 8000 samples allowed
        # repetitions: How many times the waveform is repeated. -1 means infinite
        if len(samples) == 0 or len(samples) > 8000:
            raise Exception("Invalid number of samples in AWG definition")
        for idx in range(0, len(samples), 64):
            cmd = "awg 0 0 " + " ".join([str(v) for v in samples[idx:idx+64]])
            self._sendReceive(cmd)
        self._sendReceive("run %d" % repetitions)

    def setChannelOutput(self, channel, generator, amplitude=1.0, offset=0):
        # Defines the output for a channel
        # generator: Generator.DC, Generator.generator1, .., Generator.generator8, Generator.AWG, Generator.pulsetrain
        # amplitude: Scaling of the waveform
        # offset: Voltage offset
        self._validateChannel(channel)
        if generator not in Generator.all:
            raise Exception("Invalid generator number (must be 0-10): %d" % generator)
        self._validateVoltage(channel, amplitude)
        self._validateVoltage(channel, offset)
        self._sendReceive("wav %d %d %f %f" % (channel, generator, amplitude, offset))

    def setSyncOutput(self, syncChannel, generator, delay=0, pulseLength=1):
        # Set output on a sync output channel
        # syncChannel: 0-5
        # generator: The generator that the sync channel follows
        # delay: milliseconds delay for the sync
        # pulseLength: Length in milliseconds of the sync pulse
        if syncChannel not in qdac.syncChannels:
            raise Exception("Invalid sync channel (must be 0-5): %d" % syncChannel)
        if generator not in Generator.all:
            raise Exception("Invalid generator number (must be 0-10): %d" % generator)
        if delay < 0 or delay > 268435455:
            raise Exception("Invalid sync channel delay: %d ms" % delay)
        if pulseLength < 1:
            raise Exception("Invalid sync channel pulse length: %d ms" % pulseLength)
        self._sendReceive("syn %d %d %d %d" % (syncChannel, generator, delay, pulseLength))

    def setSyncOutputOff(self, syncChannel):
        # Turns off output on a sync output channel
        # syncChannel: 0-5
        if syncChannel not in qdac.syncChannels:
            raise Exception("Invalid sync channel (must be 0-5): %d" % syncChannel)
        self._sendReceive("syn %d %d %d %d" % (syncChannel, 0, 0, 0))

    def getADCreading(self, channel):
        # Reads current from a DAC channel. Unit is in Amps
        self._validateChannel(channel)
        reply = self._sendReceive("get %d" % channel)
        return float(reply.split(":", 1)[1][:-2])*1e-6

    def waitForSync(self, generator, timeout=-1):
        # Software wait for the beginning of a generator signal
        # generator: The generator that the sync waits for
        # timeout: Max number of seconds to wait. -1 = infinite
        beginTime = time.time()
        if generator not in Generator.syncGenerators:
            raise Exception("Invalid generator number (must be 1-10): %d" % generator)
        self._sendReceive("ssy %d" % generator)
        while True:
            response = self._readLine(failOnTimeout=False)
            if response and response[0] == "#":
                return True
            if timeout > 0 and time.time() - beginTime > timeout:
                return False

    def _validateChannel(self, channel):
        if channel not in qdac.channelNumbers:
            raise Exception("Invalid channel number %d" % channel)

    def _validateVoltage(self, channel, volts):
        if volts < -self.voltageRange[channel] or volts > self.voltageRange[channel]:
            raise Exception("Invalid voltage %f" % volts)

    def _sendReceive(self, msg):
        if self.verbose:
            print(msg)
        self.sport.write(msg + "\n")
        reply = self._readLine()
        return reply

    def _readLine(self, failOnTimeout=True):
        out = ""
        c = ""
        while True:
            c = self.sport.read(1)
            if c:
                if c != "\n":
                    out += c
                else:
                    break
            else:
                if failOnTimeout and self.verbose:
                    raise Exception("Timeout!")
                break
        if self.verbose and out:
            print(out)
        return out


