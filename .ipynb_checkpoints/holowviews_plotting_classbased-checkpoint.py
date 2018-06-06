import numpy as np
import holoviews as hv
import time
from holoviews import streams
import threading
import warnings
import queue
import tkinter as tk
import queue as Queue


class GUI(threading.Thread):
    #Tkinter class for background updating of instrument values
    request_queue = Queue.Queue()
    result_queue = Queue.Queue()
    
    def __init__(self):
        threading.Thread.__init__(self)
        
    def submit_to_tkinter(self,loc, value):
        self.request_queue.put((loc, value))
        #return result_queue.get()

    t = None
    def run(self):
        #global t

        def timertick():
            try: 
                loc, value = self.request_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                #print("Updated")
                #retval = callable(*args, **kwargs)
                #result_queue.put(retval)
                tk.Label(self.t,text='%s' % (value,), borderwidth=1 ).grid(row=loc[0],column=loc[1])

            self.t.after(10, timertick)

        self.t = tk.Tk()
        self.t.configure(width=640, height=480)
        #b = tk.Button(text='test', name='button', command=exit)
        #b.place(x=0, y=0)
        timertick()
        self.t.mainloop()
        

class Overview():
    sweeping_flag = 0
    q=queue.Queue()
    points = {"x": [], "y": [], "z": np.array([])}
    thread_count = 0
    gui = GUI()
    gui.start()
    plot_thread = None
    #def update_fn(self):
    #    if not self.points["z"].size:
    #        dispsq = hv.Image(()).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
    #    else:
    #        dispsq = hv.Image((self.points["x"], self.points["y"], self.points["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
    #    return dispsq
    
    #dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
    def display(self, loc, value):
        self.gui.submit_to_tkinter(loc, np.round(value,3))
        
    def simulate_measure(self, start1, stop1, num1, start2, stop2, num2):
 
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")
            #x_data = np.arange(start1, stop1, spacing1)
            #y_data = np.arange(start2, stop2, spacing2)
            
            #Use linspace to include end points in interval and give # of points instead of step
            #Add one to number of steps for convenience. For example if you want interval [0,3] with step sizes of 1, the number of steps is 4 but now can input (3-0)/1 = 3 and get desired output 
            x_data = np.linspace(start1, stop1, num1+1)
            y_data = np.linspace(start2, stop2, num2+1)
            self.points = {"x": x_data, "y": y_data, "z":np.full((len(y_data),len(x_data)), np.nan)}  # Declaration line
            def update_fn():
                dispsq = hv.Image((self.points["x"], self.points["y"], self.points["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                return dispsq

            self.dmap_in = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
            #print('here2')
            hv.ipython.display(self.dmap_in)
            try:
                for i in range(len(x_data)):
                    for j in range(len(y_data)):
                    #data.append((i, j, i**2 + j**2))

                        time.sleep(.1)
                        #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
                        self.points['z'][j,i] =self.points['x'][i]+self.points['y'][j]
                        self.display([0,1], self.points['x'][i])
                        self.display([1,1], self.points['y'][j])
                        self.dmap_in.event()
            except KeyboardInterrupt:
                pass

            img = list(self.dmap_in.data.items())[0][1]

            return img


    
    def sweep2D(self, start1, stop1, spacing1, start2, stop2, spacing2):
        plot_thread = PlottingThread(1, "Thread-1", start1, stop1, spacing1, start2, stop2, spacing2)
        img = plot_thread.start()
        return img


    def sweep2D_inline(self,start1, stop1, spacing1, start2, stop2, spacing2):

        #create queue that data is passed through
        self.q = queue.Queue()

        x_data = np.arange(start1, stop1, spacing1)
        y_data = np.arange(start2, stop2, spacing2)
        points2 = {"x": x_data, "y": y_data, "z":np.full((len(y_data),len(x_data)), np.nan)}

        #initially check self.plotthread instead of isAlive because plot_thread is initalized to None since a thread doesn't exist yet
        if self.plot_thread and self.plot_thread.isAlive():
            self.plot_thread = PlottingThread_inline(self.thread_count, "Thread %s" % (self.thread_count,), points2, self.q, self.gui, self.plot_thread)
        else:
            self.plot_thread = PlottingThread_inline(self.thread_count, "Thread %s" % (self.thread_count,), points2, self.q, self.gui)
        
        self.thread_count += 1
        img = self.plot_thread.start()
            #plot_thread.start()
        #time.sleep(1)
        print(self.plot_thread.isAlive())
            #plot_thread.join()
        img = self.q.get()
        return img

    def get_plot(self):
        try:
            return self.q.get_nowait()
        except queue.Empty:
            print("No Plot to save!")
    
    def get_plot_running(self, wait_time =10):
        #Used to get plot of currently running measurement
        self.plot_thread.get_plot = True
        i = 0
        while self.plot_thread.get_plot:
            time.sleep(1)
            i +=1
            if i == wait_time:
                print("Waited 10 seconds without response, if measurement time is longer than this use optional argument time")
        return self.get_plot()
        

    def abort_sweep(self):
        self.plot_thread.stopflag = True
        return

    
class PlottingThread_inline (threading.Thread):
   
    def __init__(self, threadID, name, point_d, q, gui, lthread = None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.point_dict = point_d
        self.qu = q
        self.stopflag = False
        self.gui = gui
        self.get_plot = False
        self.last_thread = lthread
        
    def display(self, loc, value):
        self.gui.submit_to_tkinter(loc, np.round(value,3))
    
    def simulate_measure_inline(self):#,point_dict):
        #nonlocal dmap_in
        #global plot_thread
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message="All-NaN slice encountered")

            x_data = self.point_dict['x']
            y_data = self.point_dict['y']
            #print(point_dict)
            #point_dict['z'][0,0] = point_dict['x'][0]+point_dict['y'][0]
            print('here')
            def update_fn_in():
                dispsq = hv.Image((self.point_dict["x"], self.point_dict["y"], self.point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
                return dispsq
            dmap_in = hv.DynamicMap(update_fn_in, streams=[hv.streams.Stream.define("Dummy")()])
            print('here2')
            #print(point_dict)
            time.sleep(.1)
            
            self.qu.put(dmap_in)
            #hv.ipython.display(dmap_in)
            
            print('here2.5')
            if self.last_thread:
                print(self.last_thread)
                self.last_thread.join()
            print('here3')
            for i in range(len(x_data)):
                for j in range(len(y_data)):
                    if self.stopflag:
                        img = list(dmap_in.data.items())[0][1] #This gets the hv.Image object from a Dynamic Map
                        return img
                    if self.get_plot:
                        #img = list(dmap_in.data.items())[0][1]
                        #self.qu.put(img)
                        self.qu.put(dmap_in)
                        self.get_plot = False
                    time.sleep(.1)
                    #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
                    self.point_dict['z'][j,i] = self.point_dict['x'][i]+self.point_dict['y'][j]
                    self.display([0,1], self.point_dict['x'][i])
                    self.display([1,1], self.point_dict['y'][j])
                    dmap_in.event()

            img = list(dmap_in.data.items())[0][1]

            return img
        
    def run(self):
        #if self.last_thread:
        #    print(self.last_thread)
        #    self.last_thread.join()
        print("Starting3 " + self.name)
        #time.sleep(.1)
        warnings.filterwarnings("ignore", message="All-NaN slice encountered\n drange = (np.nanmin(data), np.nanmax(data))")
        img = self.simulate_measure_inline()#self.point_dict)
        self.qu.put(img)
        print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return
    
def initialize():
    hv.extension('bokeh')
    warnings.filterwarnings("ignore", message="All-NaN slice encountered drange\n = (np.nanmin(data), np.nanmax(data))")

def cut(image):
        tap = streams.SingleTap(source=image)

        vline = hv.DynamicMap(lambda x, y: hv.VLine(image.closest((x,0))[0] if x else 0), streams=[tap])
        hline = hv.DynamicMap(lambda x, y: hv.HLine(image.closest((0,y))[1] if y else 0), streams=[tap])

        # Declare cross-sections at PointerX location
        crosssection1 = hv.DynamicMap(lambda x, y: image.sample(x=x if x else 0), streams=[tap]).opts(norm=dict(framewise=True))#.opts(plot=dict(width = 200),norm=dict(framewise=True))
        crosssection1y = hv.DynamicMap(lambda x,y: image.sample(y=y if y else 0), streams = [tap]).opts(norm=dict(framewise=True))#.opts(plot=dict(height = 200), norm=dict(framewise=True))


        # Combine images, vline and cross-sections
        #((img1 * vline) << crosssection1) + ((img2 * vline) << crosssection2)
        return ((image * vline * hline) + crosssection1 + crosssection1y)

def cut2(image):
    #Cut with slider instead of clicking on point

    def marker(x,y):
        crosssection1 = image.sample(x=x).opts(norm=dict(framewise=True))#.opts(plot=dict(width = 200),norm=dict(framewise=True))
        crosssection1y = image.sample(y=y).opts(norm=dict(framewise=True))#.opts(plot=dict(height = 200), norm=dict(framewise=True))
        return hv.Layout(image * hv.VLine(x) * hv.HLine(y) + crosssection1+crosssection1y).cols(2)

    x_axis = np.unique(image.dimension_values(0))
    y_axis = np.unique(image.dimension_values(1))
    dmap = hv.DynamicMap(marker, kdims=['x','y']).redim.range(x=(x_axis[0],x_axis[-1]), y=(y_axis[0],y_axis[-1])).redim.step(x=(x_axis[1]-x_axis[0]), y=(y_axis[1]-y_axis[0]))

        # Declare cross-sections at PointerX location

        # Combine images, vline and cross-sections
        #((img1 * vline) << crosssection1) + ((img2 * vline) << crosssection2)
        #return ((image * vline * hline) + crosssection1 + crosssection1y)
    return dmap