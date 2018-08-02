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
   
    def __init__(self, threadID, points, dataQueue, retrQueue, instrument1, measurementInstrument, currentState =None, instrument2 = None, lthread = None):
        
        #General Python threading initialization
        threading.Thread.__init__(self)
        
        self.threadID = threadID
        
        #Dictionary of points to sweep to and of measured values
        self.point_dict = points
        
        
        #Flags to indicate aborting sweep, or returning the in-progress data
        self.stopflag = False
        self.get_plot = False
        
        #Reference to previously queued thread, such that sweep only starts when previous thread is done
        self.last_thread = lthread
        
        #Default is 1D sweep, but measure function will change this to 2D based off existence of second sweep instrument
        self.sweep2D = False
        
        #Instruments to be swept and measured
        self.inst1 = instrument1
        self.inst2 = instrument2
        self.measInst = measurementInstrument
        
        #Queue that initial DynamicMap is passed through
        self.qu = dataQueue
        
        #Queue for data to actually be passed through
        self.retrieval_queue = retrQueue
        
        #Metadata of system state when measurement starts
        self.currentState = currentState
    
    @property
    def _sweepDescription(self):
        """Automatic description that just uses sweep extents"""
        inst1_dict = self.point_dict[self.inst1.name]
        if self.sweep2D:
            inst2_dict = self.point_dict[self.inst2.name]
            return "x=%s to %s in %s steps and y=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1, min(inst2_dict), max(inst2_dict), len(inst2_dict)-1)
        
        return "x=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1)
    

    def savegen(self, result):
        """Creates savedData object of measurement data and metadata"""
        name = time.strftime('%b-%d-%Y_%H-%M-%S', time.localtime())
        return saveClass.savedData(result, self.currentState, name, self._sweepDescription)
    
    
    def save(self, savedData):
        """Input is the savedData object that is returned from a sweep. This saves the object in a pickled format as well as saves a thumbnail picture of plot"""
        save_name = savedData.name
        with open('%s.p' % (save_name,), 'wb') as file:
            pickle.dump(savedData, file)
        hv.renderer('bokeh').save(savedData.plot.options(toolbar=None), './DataThumbnails/%s' % (save_name,), fmt='png')
        return
    
    
    def measure(self):
        with warnings.catch_warnings():
            #This ignores error when plot created with all-nan data. Not sure if there's a way around this, initializing with nan allows for the full range to be displayed initially
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            warnings.filterwarnings("ignore", message = "All-NaN axis encountered")
            
            x_data = self.point_dict[self.inst1.name]
            if self.inst2:
                #With existence of second instrument, must be a 2D sweep
                self.sweep2D = True
                y_data = self.point_dict[self.inst2.name]
            
            
            
            #This defines how to update the Holoviews DynamicMap. Essentially the DynamicMap works through streams where some function can stream data into the plot. Since here we are just updating the data displayed, this function just returns a plot of the current data. Also this is ugly, but not sure how to make this cleaner.
            def update_fn():
                if self.sweep2D:
                    dispsq = hv.Image((x_data, y_data, self.point_dict[self.measInst[0].name]), kdims = [self.inst1.name, self.inst2.name], vdims = self.measInst[0].name).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                    for i in range(1,len(self.measInst)):
                        dispsq += hv.Image((x_data, y_data, self.point_dict[self.measInst[i].name]), kdims = [self.inst1.name, self.inst2.name], vdims = self.measInst[i].name).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                    
                else:
                    dispsq = hv.Curve((x_data, self.point_dict[self.measInst[0].name]), kdims = self.inst1.name, vdims = self.measInst[0].name).opts(norm=dict(framewise=True)).options(color=hv.Cycle('Colorblind').values[0])
                    for i in range(1, len(self.measInst)):
                        dispsq += hv.Curve((x_data, self.point_dict[self.measInst[i].name]), kdims = self.inst1.name, vdims = self.measInst[i].name).opts(norm=dict(framewise=True)).options(color = hv.Cycle('Colorblind').values[i])
                return dispsq
            dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
            
            #This particular sleep may not be needed, but in general when using background threads without blocking in main thread, may not get expected behavior when running functions in main thread.
            time.sleep(.1)
            
            #Send DynamicMap to main thread to be displayed
            self.qu.put(dmap)
            #This sleep helps fix some issues where main thread plot wouldn't show updates
            time.sleep(1)
            
            #Block thread until previous thread (ie measurement finished)
            if self.last_thread:
                
                self.last_thread.join()
            
            
            #Different blocks for 2D vs 1D sweep, but intuitively seems unnecessary. Also makes it harder to modify, since have to modify both blocks. 
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
                            #data = self.save2D(img,1, min(x_data), max(x_data), 2, min(y_data), max(y_data))
                            data = self.savegen(img)
                            #self.qu.put(img)
                            self.sendData(data)
                            self.get_plot = False
                        
                        #Ramp y axis instrument
                        self.inst2.ramp(y_data[j])
                        
                        #This wait necessary for instantaneous ramping and measuring of instruments but for real instruments + lock in there will inherently be a wait time so probably not necessary there?
                        time.sleep(.1)
                        
                        for inst in self.measInst:
                            #For each measurement instrument provided measure
                            self.point_dict[inst.name][j,i] = inst.measure()
                        
                        #Update DynamicMap with updated data (basically just calls update_fn again)
                        dmap.event()
                        
                
                img = update_fn()
                return img
            
            else:
                for i in range(len(x_data)):
                    self.inst1.ramp(x_data[i])
                    if self.stopflag:
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
                    time.sleep(.1)
                    
                    for inst in self.measInst:
                        self.point_dict[inst.name][i] = inst.measure()
                    #measurementData[i] = self.measInst.measure()
                    
                    dmap.event()
                    
                
                img = update_fn()
                return img
            
    
        
        
    def sendData(self, data):
        """Put data into queue as only object, by first repeatedly pulling from queue until empty. Want queue to be empty because user may not always retrieve from queue after every sweep, and expected behavior is that retrieving from queue should get the latest sweep"""
        
        #Empty retrieval queue before putting data in (as long as main thread isn't putting stuff in simultaneously I think this should be fine since other threads are blocked until this thread finishes)
        while(1):
            try:
                self.retrieval_queue.get_nowait()
            except queue.Empty:
                break
        self.retrieval_queue.put(data)
    
    def run(self):
        """This defines what the thread does when started. First starts the measurement function, and when finished returns the finished plot, puts it into the savedData object, and puts the object in the queue for the main thread to retrieve. Finally it saves the object into a pickle format to be read earlier. The measure function itself sends the empty plot to the main thread which is then updated."""

        img = self.measure()
        
        if img:
            data = self.savegen(img)
            
            self.sendData(data)
            #print(data.state)
            self.save(data)
        #print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return
    

class PlottingOverview():
    """This object manages the different plotting threads for every sweep"""
      
    #Define queues to send plot + data through
    q=queue.Queue()
    retrieval_queue = queue.Queue()
    
    #Initialize thread ID number
    thread_count = 0
    
    #This keeps track of the last queued sweep thread (not necessarily the currently running sweep)
    plot_thread = None
    
    def _sweep(self, inst1, measInst, points, currState, inst2 = None):
        #create queue that data is passed through
        self.q = queue.Queue()
        
        #If last queued sweep thread is still running, then pass as the last thread for new sweep thread to reference (such that it waits for that thread to finish before running)
        
        #Inputs of plot thread are the thread ID, dictionary of data, two queues, instruments to be swept, instruments to be measured, reference to previous thread (if applicable), and current state of all instruments 
        if self.plot_thread and self.plot_thread.isAlive():
            self.plot_thread = PlottingThread(self.thread_count, points, self.q, self.retrieval_queue, instrument1 = inst1, instrument2 = inst2, measurementInstrument = measInst, lthread = self.plot_thread, currentState = currState)
        else:
            self.plot_thread = PlottingThread(self.thread_count, points, self.q, self.retrieval_queue, instrument1 = inst1, instrument2 = inst2, measurementInstrument = measInst, currentState = currState)
        
        #Increase thread count so next thread has different ID
        self.thread_count += 1
        
        #Starts thread by executing its run function
        self.plot_thread.start()
            
        #Retrieve image placed in queue by plotting thread
        #Using .get instead of no wait because .get blocks until it actually gets an object
        img = self.q.get()
        #self.plot_thread.join() #Temporary, used to see this plots full outputs
        return img


    def _getPlot(self):
        try:
            return self.retrieval_queue.get_nowait()
        except queue.Empty:
            print("No Plot to get!")
        
    
    def _getPlotRunning(self, wait_time =10):
        #Used to get plot of currently running measurement
        curr_thread = self._runningThread
        curr_thread.get_plot = True
        i = 0
        while curr_thread.get_plot:
            time.sleep(1)
            i +=1
            if i == wait_time:
                print("Waited 10 seconds without response, if measurement time of a point is longer than this use optional argument wait_time")     
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
        curr_thread = self._runningThread
        curr_thread.stopflag = True
        return
    
    def abort_all(self):
        curr_thread = self.plot_thread
        while curr_thread.last_thread and curr_thread.last_thread.isAlive():
            curr_thread.stopflag = True
            curr_thread = curr_thread.last_thread
        curr_thread.stopflag = True
        return
    
    @property
    def current_queue(self):
        queue_list = []
        curr_thread = self.plot_thread
        while curr_thread and curr_thread.isAlive():
            queue_list.append("ID %s: " % (curr_thread.threadID,) + curr_thread._sweepDescription)
            curr_thread = curr_thread.last_thread
        #queue_list.append(curr_thread._sweepDescription)
        for sweep in queue_list[::-1]:
            print(sweep)
        return
    
    def abortSweepID(self, id):
        """Abort the given sweep ID, whether it is currently running or in the queue"""
        curr_thread = self.plot_thread
        prev_thread = None
        while curr_thread and curr_thread.isAlive():
            if curr_thread.threadID == id:
                curr_thread.stopflag = True
                if prev_thread:
                    prev_thread.last_thread = curr_thread.last_thread
                else:
                    self.plot_thread = curr_thread.last_thread
                return "Sweep ID %s aborted" % (id,)
            prev_thread = curr_thread
            curr_thread = curr_thread.last_thread
        return "No queued sweep with ID %s!" % (id,)
    