import warnings
import holoviews as hv
import time
import numpy as np
import threading
import saveClass
import pickle
import queue

class PlottingThread_inline (threading.Thread):
   
    def __init__(self, threadID, name, point_d, data_queue, retr_queue, gui, qdevil, lthread = None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.point_dict = point_d
        self.qu = data_queue
        self.stopflag = False
        self.gui = gui
        self.get_plot = False
        self.last_thread = lthread
        self.qd = qdevil
        self.retrieval_queue = retr_queue
        self.sweep2D = False
    
    @property
    def _sweepDescription(self):
        """Automatic description that just uses sweep extents"""
        if self.sweep2D:
            return "x=%s to %s in %s steps and y=%s to %s in %s steps" % (min(self.point_dict['x']), max(self.point_dict['x']), len(self.point_dict['x'])-1, min(self.point_dict['y']), max(self.point_dict['y']), len(self.point_dict['y'])-1)
        
        return "x=%s to %s in %s steps" % (min(self.point_dict['x']), max(self.point_dict['x']), len(self.point_dict['x'])-1)
    
    def display_voltage(self, loc, value):
        """Send voltage to Tkinter table to be displayed"""
        self.gui.submit_to_tkinter(loc, np.round(value,6))
        return
    
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
    
    
    def simulate_measure_inline(self):#,point_dict):
        #nonlocal dmap_in
        #global plot_thread
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")

            x_data = self.point_dict['x']
            y_data = self.point_dict['y']
            if 'z' in self.point_dict:
                self.sweep2D = True
            

            def update_fn_in():
                if self.sweep2D:
                    dispsq = hv.Image((self.point_dict["x"], self.point_dict["y"], self.point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                else:
                    dispsq = hv.Curve((self.point_dict["x"], self.point_dict["y"])).opts(norm=dict(framewise=True))
                return dispsq
            dmap_in = hv.DynamicMap(update_fn_in, streams=[hv.streams.Stream.define("Dummy")()])
            
            time.sleep(.1)
            
            self.qu.put(dmap_in)
            time.sleep(1)
            if self.last_thread:
                print(self.last_thread.threadID)
                self.last_thread.join()
            
            if self.sweep2D:
                for i in range(len(x_data)):

                    for j in range(len(y_data)):
                        if self.stopflag:
                            if not np.isnan(self.point_dict['z']).all():
                                #create another copy of the image because dynamic map object now exists in main thread
                                img = hv.Image((self.point_dict["x"], self.point_dict["y"], self.point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))

                                return img
                            return
                        if self.get_plot:
                            #Used to get plot while its running
                            img = hv.Image((self.point_dict["x"], self.point_dict["y"], self.point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                            data = self.save2D(img,1, min(self.point_dict['x']), max(self.point_dict['x']), 2, min(self.point_dict['y']), max(self.point_dict['y']))
                            #self.qu.put(img)
                            self.sendData(data)
                            self.get_plot = False
                        time.sleep(.1)
                        #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
                        self.point_dict['z'][j,i] = self.point_dict['x'][i]+self.point_dict['y'][j]
                        #print('g')

                        #Push value to tkinter (voltage table) Format is [channel #, 2]; column order is channel # (0), name (1), voltage (2)
                        self.display_voltage([1,2], self.point_dict['x'][i])
                        self.display_voltage([2,2], self.point_dict['y'][j])
                        dmap_in.event()
                        #print('h')
                img = hv.Image((self.point_dict["x"], self.point_dict["y"], self.point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                return img
            
            else:
                for i in range(len(x_data)):
                    if self.stopflag:
                        if not np.isnan(self.point_dict['y']).all():
                                #create another copy of the image because dynamic map object now exists in main thread
                            img = hv.Curve((self.point_dict["x"], self.point_dict["y"])).opts(norm=dict(framewise=True))

                            return img
                        return
                    if self.get_plot:
                        #Used to get plot while its running
                        img = hv.Curve((self.point_dict["x"], self.point_dict["y"])).opts(norm=dict(framewise=True))
                        data = self.save1D(img,1, min(self.point_dict['x']), max(self.point_dict['x']))
                            #self.qu.put(img)
                        self.sendData(data)
                        self.get_plot = False
                    time.sleep(.1)
                    #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
                    self.point_dict['y'][i] = self.point_dict['x'][i]**2
                    

                    #Push value to tkinter (voltage table) Format is [channel #, 2]; column order is channel # (0), name (1), voltage (2)
                    self.display_voltage([1,2], self.point_dict['x'][i])
                    dmap_in.event()
                        #print('h')
                img = hv.Curve((self.point_dict["x"], self.point_dict["y"])).opts(norm=dict(framewise=True))
                return img
        
        
    def sendData(self, data):
        while(1):
            try:
                self.retrieval_queue.get_nowait()
            except queue.Empty:
                break
        self.retrieval_queue.put(data)
    
    def run(self):
   
        #print("Starting " + self.name)
        #time.sleep(.1)
        warnings.filterwarnings("ignore", message="All-NaN slice encountered\n drange = (np.nanmin(data), np.nanmax(data))")
        img = self.simulate_measure_inline()

        if img:
            data = self.save2D(img,1, min(self.point_dict['x']), max(self.point_dict['x']), 2, min(self.point_dict['y']), max(self.point_dict['y']))
            #self.save(data)
            
            #Empty retrieval queue before putting data in (as long as main thread isn't putting stuff in simultaneously I think this should be fine since other threads are blocked until this thread finishes)
            self.sendData(data)
            #print(data.state)
            self.save(data)
        #print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return
    