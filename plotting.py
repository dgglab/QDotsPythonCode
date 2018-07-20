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
   
    def __init__(self, threadID, name, points, dataQueue, retrQueue, instrument1, measurementInstrument, currentState =None, instrument2 = None, lthread = None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.point_dict = points
        self.qu = dataQueue
        self.stopflag = False
        self.get_plot = False
        self.last_thread = lthread
        self.inst1 = instrument1
        self.inst2 = instrument2
        self.measInst = measurementInstrument
        self.retrieval_queue = retrQueue
        self.sweep2D = False
        self.currentState = currentState
    
    @property
    def _sweepDescription(self):
        """Automatic description that just uses sweep extents"""
        inst1_dict = self.point_dict[self.inst1._name]
        if self.sweep2D:
            inst2_dict = self.point_dict[self.inst2._name]
            return "x=%s to %s in %s steps and y=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1, min(inst2_dict), max(inst2_dict), len(inst2_dict)-1)
        
        return "x=%s to %s in %s steps" % (min(inst1_dict), max(inst1_dict), len(inst1_dict)-1)
    

    def savegen(self, result):
        name = time.strftime('%b-%d-%Y_%H-%M-%S', time.localtime())
        return saveClass.savedData(result, self.currentState, name, self._sweepDescription)
    
    def save2D(self,result, channel1, start1, stop1, channel2, start2,stop2):
        """Use result and sweep extents to save into the savedData class"""
        curr_state = self.qd._convertDF()
        
        
        ch1 = self.qd._parseChannel(channel1)[0]
        ch2 = self.qd._parseChannel(channel2)[0]

        #This is just pandas syntax to index a particular location (uses name of row, column) I believe can also use numbers, but if order of rows ever change, the name indexing won't change
        curr_state.loc['Channel %s' % (ch1,), 'Voltage'] = '%s to %s' % (start1, stop1) 
        curr_state.loc['Channel %s' % (ch2,), 'Voltage'] = '%s to %s' % (start2, stop2)
        
        t = time.localtime()
        name = time.strftime('%b-%d-%Y_%H-%M-%S', t)
        return saveClass.savedData(result, curr_state, name, self._sweepDescription)

    def save1D(self,result, channel1, start1, stop1):
        curr_state =self.qd._convertDF()
        ch1 = self.qd._parseChannel(channel1)[0]

        #b.loc['Channel %s' % (ch1,), 'Channel Name'] = 'Small Dot Gate'
        curr_state.loc['Channel %s' % (ch1,), 'Voltage'] = '%s to %s' % (start1, stop1) 
        t = time.localtime()
        name = time.strftime('%b-%d-%Y_%H:%M:%S', t)

        return saveClass.savedData(result, curr_state, name, self._sweepDescription)
    
    def save(self, savedData):
        """Input is the savedData object that is returned from a sweep."""
        save_name = savedData.name
        with open('%s.p' % (save_name,), 'wb') as file:
            pickle.dump(savedData, file)
        hv.renderer('bokeh').save(savedData.plot.options(toolbar=None), './DataThumbnails/%s' % (save_name,), fmt='png')
        return
    
    
    def measure(self):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            
            x_data = self.point_dict[self.inst1._name]
            if self.inst2:
                self.sweep2D = True
                y_data = self.point_dict[self.inst2._name]
            
            
            
            #This defines how to update the Holoviews DynamicMap. Essentially the DynamicMap works through streams where some function can stream data into the plot. Since here we are just updating the data displayed, this function just returns a plot of the current data.
            def update_fn():
                if self.sweep2D:
                    dispsq = hv.Image((x_data, y_data, self.point_dict[self.measInst[0]._name]), kdims = [self.inst1._name, self.inst2._name], vdims = self.measInst[0]._name).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                    for i in range(1,len(self.measInst)):
                        dispsq += hv.Image((x_data, y_data, self.point_dict[self.measInst[i]._name]), kdims = [self.inst1._name, self.inst2._name], vdims = self.measInst[i]._name).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                    
                else:
                    dispsq = hv.Curve((x_data, self.point_dict[self.measInst[0]._name]), kdims = self.inst1._name, vdims = self.measInst[0]._name).opts(norm=dict(framewise=True)).options(color=hv.Cycle('Colorblind').values[0])
                    for i in range(1, len(self.measInst)):
                        dispsq += hv.Curve((x_data, self.point_dict[self.measInst[i]._name]), kdims = self.inst1._name, vdims = self.measInst[i]._name).opts(norm=dict(framewise=True)).options(color = hv.Cycle('Colorblind').values[i])
                return dispsq
            dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
            
            #This particular sleep may not be needed, but in genearl when using background threads without blocking in main thread, may not get expected behavior when running functions in main thread.
            time.sleep(.1)
            self.qu.put(dmap)
            time.sleep(1)
            #Block thread until previous thread (ie measurement finished)
            if self.last_thread:
                #print(self.last_thread.threadID)
                self.last_thread.join()
            
            
            if self.sweep2D:
                for i in range(len(x_data)):
                    self.inst1.ramp(x_data[i])
                    for j in range(len(y_data)):
                        if self.stopflag:
                            if not np.isnan(self.point_dict[self.measInst[0]._name]).all():
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
                        
                        self.inst2.ramp(y_data[j])
                        time.sleep(.1)
                        
                        for inst in self.measInst:
                            self.point_dict[inst._name][j,i] = inst.measure()
                        
                        #Update DynamicMap with updated data
                        dmap.event()
                        
                
                img = update_fn()
                return img
            
            else:
                for i in range(len(x_data)):
                    self.inst1.ramp(x_data[i])
                    if self.stopflag:
                        if not np.isnan(self.point_dict[self.measInst[0]._name]).all():
                                #create another copy of the image because dynamic map object now exists in main thread
                            
                            img = update_fn()
                            return img
                        return
                    if self.get_plot:
                        #Used to get plot while its running
                        
                        img = update_fn()
                        #data = self.save1D(img,1, min(x_data), max(x_data))
                        data = self.savegen(img)
                        self.sendData(data)
                        self.get_plot = False
                    time.sleep(.1)
                    
                    for inst in self.measInst:
                        self.point_dict[inst._name][i] = inst.measure()
                    #measurementData[i] = self.measInst.measure()
                    
                    dmap.event()
                    
                
                img = update_fn()
                return img
            
    
        
        
    def sendData(self, data):
        """Put data into queue as only object, by first repeatedly pulling from queue until empty. Want queue to be empty because user may not always retrieve from queue after every sweep, and expected behavior is that retrieving from queue should get the latest sweep"""
        while(1):
            try:
                self.retrieval_queue.get_nowait()
            except queue.Empty:
                break
        self.retrieval_queue.put(data)
    
    def run(self):
        """This defines what the thread does when started. First starts the measurement function which returns the finished plot, puts it into the savedData object, and puts the object in the queue for the main thread to retrieve. Finally it saves the object into a pickle format to be read earlier."""
        #print("Starting " + self.name)
        
        warnings.filterwarnings("ignore", message="All-NaN slice encountered\n drange = (np.nanmin(data), np.nanmax(data))")
        img = self.measure()
        
        
        #x_data = self.point_dict[self.inst1._name]
        #xmin = min(x_data)
        #xmax = max(x_data)
        #if self.inst2:
        #    y_data = self.point_dict[self.inst2._name]
        #    ymin = min(y_data)
        #    ymax = max(y_data)
        #if img:
        #    if self.sweep2D:
        #        data = self.save2D(img,1, xmin, xmax, 2, ymin, ymax)
        #        
        #    else:
        #        data = self.save1D(img, 1, xmin, xmax)
        
        if img:
            data = self.savegen(img)
            
            #Empty retrieval queue before putting data in (as long as main thread isn't putting stuff in simultaneously I think this should be fine since other threads are blocked until this thread finishes)
            self.sendData(data)
            #print(data.state)
            self.save(data)
        #print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return
    

class PlottingOverview():
    sweeping_flag = 0
    
    q=queue.Queue()
    retrieval_queue = queue.Queue()
    
    
    thread_count = 0
    plot_thread = None
    
    def _sweep(self, inst1, measInst, points, currState, inst2 = None):
        #create queue that data is passed through
        self.q = queue.Queue()
        
        
        if self.plot_thread and self.plot_thread.isAlive():
            self.plot_thread = PlottingThread(self.thread_count, "Thread %s" % (self.thread_count,), points, self.q, self.retrieval_queue, instrument1 = inst1, instrument2 = inst2, measurementInstrument = measInst, last_thread = self.plot_thread, currentState = currState)
        else:
            self.plot_thread = PlottingThread(self.thread_count, "Thread %s" % (self.thread_count,), points, self.q, self.retrieval_queue, instrument1 = inst1, instrument2 = inst2, measurementInstrument = measInst, currentState = currState)
        
        self.thread_count += 1
        self.plot_thread.start()
            
        #time.sleep(.1)
        #Using .get instead of no wait because .get blocks until it actually gets an object
        img = self.q.get()
        #self.plot_thread.join() #Temporary, used to see this plots full outputs
        #time.sleep(.1)
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
    