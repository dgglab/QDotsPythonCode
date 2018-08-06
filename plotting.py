import warnings
import holoviews as hv
import time
import numpy as np
import threading
import saveClass
import pickle
import queue
import numpy as np


class PlottingThread(threading.Thread):
    def __init__(self, threadID, points, dataQueue, retrQueue, instrument1,
                measurementInstrument, currentState =None, instrument2 = None,
                lthread = None):
        """Thread object that handles background sweeping and measuring of
		instruments.
        
        Args:
            threadID: Unique thread ID given to each thread. Allows for ability
                to abort a specific thread by ID.
            
            points: Dictionary of points to sweep to and also contains an np.nan
                initialized array of measurement data. Measurement data array shape should be length(instrument2) x length(instrument1) Format is roughly {instrumentName: [points to sweep], measurementInstName: [[np.nan,...,np.nan],...]}
            
            dataQueue: Python Queue object that initial Holoviews DynamicMap is
                passed through in order to display updating plot in main thread.
            
            retrQueue: Python Queue object that savedData object is passed
                through when measurement complete or when called for by main thread.
            
            instrument1: The instrument to be swept on the x-axis
                (slow axis for 2D sweep). This should be the instrument object
                itself.
            
            measurementInstrument: The instrument to be measured at each point.
                This can be a list of instruments if multiple parameters are being measured.
            
            currentState: Metadata of full system state. This is usually
                obtained from the Measurement object (in measure.py) currentState method
            
            instrument2: For 2D sweeps, this is the instrument on the y-axis
                (fast axis). This should be the instrument object itself.
            
            lthread: Reference to the thread initialized previous to this one.
                This is used to ensure that the sweep only starts when the
                previous thread is finished.
            
        """
        #General Python threading initialization
        threading.Thread.__init__(self)
        
        self.threadID = threadID
        self.point_dict = points
        
        #Flags to indicate aborting sweep, or returning the in-progress data
        self.stopflag = False
        self.get_plot = False
        
        self.last_thread = lthread
        
        #Default is 1D sweep, but measure function will change this to 2D based
		#off existence of second sweep instrument
        self.sweep2D = False
        
        self.inst1 = instrument1
        self.inst2 = instrument2
        self.measInst = measurementInstrument
        
        self.qu = dataQueue
        self.retrieval_queue = retrQueue
        
        self.currentState = currentState
    
    @property
    def _sweepDescription(self):
        """Automatic description that just uses sweep extents. Returns
        description as string"""
        inst1_dict = self.point_dict[self.inst1.name]
        if self.sweep2D:
            inst2_dict = self.point_dict[self.inst2.name]
            return "x=%s to %s in %s steps and y=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1, min(inst2_dict), max(inst2_dict), len(inst2_dict)-1)
        
        return "x=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1)
    
    def savegen(self, result):
        """Creates savedData object of measurement data and metadata, and uses
        current time as the name. Returns savedData object
        
        Args:
            result: The plot to be saved. Typically is a Holoviews Curve
                (for 1D sweep) or Image (for 2D sweep), but does not have to be
		"""
        name = time.strftime('%b-%d-%Y_%H-%M-%S', time.localtime())
        return saveClass.savedData(result, self.currentState, name, self._sweepDescription)
    
    def save(self, savedData):
        """Saves a savedData object as pickle file. Also saves a picture of the
        plot to be used as a thumbnail.
        
        Args:
            savedData: savedData object containing data and metadata information
        """
        save_name = savedData.name
        with open('%s.p' % (save_name,), 'wb') as file:
            pickle.dump(savedData, file)
        hv.renderer('bokeh').save(savedData.plot.options(toolbar=None), './DataThumbnails/%s' % (save_name,), fmt='png')
    
    def measure(self):
        """Main function run by thread. This creates the Holoviews DynamicMap,
        ramps instruments to given values, measures, and then updates plot. 
        Two flags are checked, one whether to send the current plot to the main
        thread for retreival, and another to check whether to abort. Returns the
        completed (or aborted) Holoviews Curve or Image.
        """
        with warnings.catch_warnings():
            #This ignores error when plot created with all-nan data. Not sure if
			#there's a way around this, initializing with nan allows for the
			#full range to be displayed initially
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            warnings.filterwarnings("ignore", message = "All-NaN axis encountered")
            
            x_data = self.point_dict[self.inst1.name]
            if self.inst2:
                #With existence of second instrument, must be a 2D sweep
                self.sweep2D = True
                y_data = self.point_dict[self.inst2.name]
            
            #This defines how to update the Holoviews DynamicMap. Essentially
			#the DynamicMap works through streams where some function can stream data into the plot. Since here we are just updating the data displayed, this function just returns a plot of the current data. Also this is ugly, but not sure how to make this cleaner.
            def update_fn():
                if self.sweep2D:
                    dispsq = hv.Image((x_data, y_data,
                                        self.point_dict[self.measInst[0].name]),
                                        kdims=[self.inst1.name, self.inst2.name],
                                        vdims=self.measInst[0].name).opts(norm=dict(framewise=True),
                                                                        plot=dict(colorbar=True),
                                                                        style=dict(cmap='jet'))
                    for i in range(1,len(self.measInst)):
                        dispsq += hv.Image((x_data, y_data,
                                        self.point_dict[self.measInst[i].name]),
                                        kdims=[self.inst1.name, self.inst2.name],
                                        vdims=self.measInst[i].name).opts(norm=dict(framewise=True),
                                                                        plot=dict(colorbar=True),
                                                                        style=dict(cmap='jet'))
                    
                else:
                    dispsq = hv.Curve((x_data,
                                    self.point_dict[self.measInst[0].name]),
                                    kdims=self.inst1.name,
                                    vdims=self.measInst[0].name).options(framewise=True,
                                    color=hv.Cycle('Colorblind').values[0])
                    for i in range(1, len(self.measInst)):
                        dispsq += hv.Curve((x_data,
                                            self.point_dict[self.measInst[i].name]), 
                                            kdims=self.inst1.name,
                                            vdims=self.measInst[i].name).options(framewise=True,
                                                                                color=hv.Cycle('Colorblind').values[i])
                return dispsq
            dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
            
            #This particular sleep may not be needed, but in general when using
            #background threads without blocking in main thread, may not get
            #expected behavior when running functions in main thread.
            time.sleep(.1)
            
            #Send DynamicMap to main thread to be displayed
            self.qu.put(dmap)
            #This sleep helps fix some issues where main thread plot wouldn't
            #show updates
            time.sleep(1)
            
            #Block thread until all previous threads are finished. I don't just
            #check last thread here, in case one thread dies unexpectedly in the
            #middle of a queue and another is still running
            curr_thread = self.last_thread
            while curr_thread:
                curr_thread.join()
                curr_thread = curr_thread.last_thread
                
            #Different blocks for 2D vs 1D sweep, but intuitively seems
            #unnecessary. Also makes it harder to modify, since have to modify
            #both blocks. 
            if self.sweep2D:
                for i in range(len(x_data)):
                    #Ramp x axis instrument
                    self.inst1.ramp(x_data[i])
                    for j in range(len(y_data)):
                        if self.stopflag:
                            
                            #Only return plot if a point has already been measured
                            if not np.isnan(self.point_dict[self.measInst[0].name]).all():
                                #create another copy of the image because dynamic map object now exists in main thread
                                img = update_fn()

                                return img
                            return
                        if self.get_plot:
                            #Used to get plot while its running
                            img = update_fn()
                            data = self.savegen(img)
                            self.sendData(data)
                            self.get_plot = False
                        
                        #Ramp y axis instrument
                        self.inst2.ramp(y_data[j])
                        
                        #This wait necessary for instantaneous ramping and
                        #measuring of instruments but for real
                        #instruments + lock in there will inherently be a wait
                        #time so probably not necessary there?
                        time.sleep(.1)
                        
                        for inst in self.measInst:
                            #For each measurement instrument provided measure
                            self.point_dict[inst.name][j,i] = inst.measure()
                        
                        #Update DynamicMap with updated data (basically just
                        #calls update_fn again)
                        dmap.event()
                img = update_fn()
                return img
            
            else:
                for i in range(len(x_data)):
                    self.inst1.ramp(x_data[i])
                    if self.stopflag:
                        if not np.isnan(self.point_dict[self.measInst[0].name]).all():
                            #create another copy of the image because
                            #dynamic map object now exists in main thread
                            img = update_fn()
                            return img
                        return
                    if self.get_plot:
                        #Used to get plot while its running
                        img = update_fn()
                        data = self.savegen(img)
                        self.sendData(data)
                        self.get_plot = False
                    time.sleep(.1)
                    
                    for inst in self.measInst:
                        self.point_dict[inst.name][i] = inst.measure()
                    dmap.event()

                img = update_fn()
                return img
            
    def sendData(self, data):
        """Put data into queue as only object, by first repeatedly pulling from
        queue until empty. Want queue to be empty because user may not always
        retrieve from queue after every sweep, and expected behavior is that
        retrieving from queue should get the latest sweep
        """
        
        #Empty retrieval queue before putting data in (as long as main thread
        #isn't putting stuff in simultaneously I think this should be fine since
        #other threads are blocked until this thread finishes)
        while(1):
            try:
                self.retrieval_queue.get_nowait()
            except queue.Empty:
                break
        self.retrieval_queue.put(data)
    
    def run(self):
        """This defines what the thread does when started. First starts the
        measurement function, and when finished returns the finished plot, puts
        it into the savedData object, and puts the object in the queue for the
        main thread to retrieve. Finally it saves the object into a pickle
        format to be read earlier. The measure function itself sends the empty
        plot to the main thread which is then updated.
        """
        img = self.measure()
        if img:
            data = self.savegen(img)
            self.sendData(data)
            #print(data.state)
            self.save(data)
        return img
    
    def stop(self):
        return
    

class PlottingOverview():
    """This object manages the different plotting threads for every sweep.
    This is also used by Measurement object to access plotting threads in order
	to retrieve data or abort threads
	"""
    #Define queues to send plot + data through
    q=queue.Queue()
    retrieval_queue = queue.Queue()
    
    #Initialize thread ID number
    thread_count = 0
    
    #This keeps track of the last queued sweep thread (not necessarily the
	#currently running sweep)
    plot_thread = None
    
    def _sweep(self, inst1, measInst, points, currState, inst2 = None):
        """Creates and starts PlottingThread with instruments to be swept.
        Returns the DynamicMap the thread puts into a queue, such that main
        thread can display.
        
        Args:
            inst1: Instrument to be swept on x-axis
            
            measInst: Intrument (or list of instruments) to be measured
            
            points: Dictionary of values to sweep to for each instrument as well
                as array of measurement data
            
            currState: Metadata of current state of all instruments in system
            
            inst2: Instrument to be swept on y-axis (fast axis) for a 2D sweep
        """
        #Create new queue, since old one might still have data that was never retrieved
        self.q = queue.Queue()
        
        #If last queued sweep thread is still running, then pass as the last
        #thread for new sweep thread to reference (such that it waits for that
        #thread to finish before running)
  
        if self.plot_thread and self.plot_thread.isAlive():
            self.plot_thread = PlottingThread(self.thread_count, points, self.q,
                                            self.retrieval_queue, inst1,
                                            measInst, currState, inst2,
                                            lthread = self.plot_thread)
        else:
            self.plot_thread = PlottingThread(self.thread_count, points, self.q,
                                            self.retrieval_queue, inst1,
                                            measInst, currState, inst2)
        
        #Increase thread count so next thread has different ID
        self.thread_count += 1
        
        #Starts thread by executing its run function
        self.plot_thread.start()
            
        #Retrieve image placed in queue by plotting thread
        #Using .get instead of no wait because .get blocks until it actually
        #gets an object
        img = self.q.get()
        return img


    def _getPlot(self):
        """Returns savedData object from last completed sweep."""
        try:
            return self.retrieval_queue.get_nowait()
        except queue.Empty:
            print("No Plot to get!")
        
    
    def _getPlotRunning(self, wait_time=10):
        """Returns data from currently running thread"""
        curr_thread = self._runningThread
        curr_thread.get_plot = True
        i = 0
        while curr_thread.get_plot:
            time.sleep(1)
            i +=1
            if i == wait_time:
                print("Waited %s seconds without response, if measurement time of a point is longer than this use optional argument wait_time" % (wait_time,))     
                return
        return self._getPlot()
        

    @property
    def _runningThread(self):
        """Returns the currently running thread"""
        curr_thread = self.plot_thread
        while curr_thread.last_thread and curr_thread.last_thread.isAlive():
            curr_thread = curr_thread.last_thread
        return curr_thread
    
    def abort_sweep(self):
        """Aborts the currently running sweep"""
        curr_thread = self._runningThread
        curr_thread.stopflag = True
        return
    
    def abort_all(self):
        """Aborts all queued sweeps"""
        curr_thread = self.plot_thread
        while curr_thread.last_thread and curr_thread.last_thread.isAlive():
            curr_thread.stopflag = True
            curr_thread = curr_thread.last_thread
        curr_thread.stopflag = True
        return
    
    @property
    def current_queue(self):
        """Prints each thread currently in queue along with the associated ID"""
        queue_list = []
        curr_thread = self.plot_thread
        while curr_thread and curr_thread.isAlive():
            queue_list.append("ID %s: " % (curr_thread.threadID,) + curr_thread._sweepDescription)
            curr_thread = curr_thread.last_thread
        for sweep in queue_list[::-1]:
            print(sweep)
        return
    
    def abortSweepID(self, ID):
        """Abort the given sweep ID, whether it is currently running or in the
		queue
        
        Args:
            ID: ID of sweep to be aborted
		"""
        curr_thread = self.plot_thread
        prev_thread = None
        while curr_thread and curr_thread.isAlive():
            if curr_thread.threadID == ID:
                curr_thread.stopflag = True
                if prev_thread:
                    prev_thread.last_thread = curr_thread.last_thread
                else:
                    self.plot_thread = curr_thread.last_thread
                print("Sweep ID %s aborted" % (ID,))
                return
            prev_thread = curr_thread
            curr_thread = curr_thread.last_thread
        print("No queued sweep with ID %s!" % (ID,))
        return
    
    @property
    def currentlyRunning(self):
        """Returns True if there is currently an actively running thread.
        Used to ensure main thread does not try to use instruments during a
        sweep. Note this only checks the last thread in queue, which is not
        necessarily the one that is currently sweeping instruments, but can be
        paused waiting for previous threada to finish
        """
        if self.plot_thread and self.plot_thread.isAlive():
            return True
        return False