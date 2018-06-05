import numpy as np
import holoviews as hv
import time
from holoviews import streams
import threading
import warnings
import queue

sweeping_flag = 0

points = {"x": [], "y": [], "z": np.array([])} 
def update_fn():
    global points
    if not points["z"].size:
        dispsq = hv.Image(()).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
    else:
        dispsq = hv.Image((points["x"], points["y"], points["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
    return dispsq
dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])



def initialize():
    hv.extension('bokeh')
    warnings.filterwarnings("ignore", message="All-NaN slice encountered drange\n = (np.nanmin(data), np.nanmax(data))")
    #return dmap

def simulate_measure(start1, stop1, spacing1, start2, stop2, spacing2):
    global points
    global dmap
    hv.ipython.display(dmap)
    x_data = np.arange(start1, stop1, spacing1)
    y_data = np.arange(start2, stop2, spacing2)
    points = {"x": x_data, "y": y_data, "z":np.full((len(y_data),len(x_data)), np.nan)}  # Declaration line
    #dmap.event()
    #def update_fn(): 
    #    dispsq = hv.Image((points["x"], points["y"], points["z"]))
    #    return dispsq
    #dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
    #dmap
    for i in range(len(x_data)):
        for j in range(len(y_data)):
        #data.append((i, j, i**2 + j**2))
            time.sleep(.1)
            #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
            points['z'][j,i] =points['x'][i]+points['y'][j]
            dmap.event()
            
    img = list(dmap.data.items())[0][1]
    
    return img

def simulate_measure_inline(point_dict):
    #nonlocal dmap_in
    global plot_thread
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message="All-NaN slice encountered")
        
        x_data = point_dict['x']
        y_data = point_dict['y']
        #print(point_dict)
        #point_dict['z'][0,0] = point_dict['x'][0]+point_dict['y'][0]
        print('here')
        def update_fn_in():
            dispsq = hv.Image((point_dict["x"], point_dict["y"], point_dict["z"])).opts(norm=dict(framewise=True), plot=dict(colorbar=True), style=dict(cmap='jet'))
            return dispsq
        dmap_in = hv.DynamicMap(update_fn_in, streams=[hv.streams.Stream.define("Dummy")()])
        print('here2')
        #print(point_dict)
        hv.ipython.display(dmap_in)
        print('here3')
        for i in range(len(x_data)):
            for j in range(len(y_data)):
                if plot_thread.stopflag:
                    img = list(dmap_in.data.items())[0][1]
                    return img
                time.sleep(.1)
                #points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
                point_dict['z'][j,i] =point_dict['x'][i]+point_dict['y'][j]
                dmap_in.event()

        img = list(dmap_in.data.items())[0][1]

        return img

def sweep1D(start, stop, spacing):
    return

#def measure_mp(start1, stop1, spacing1, start2, stop2, spacing2, q):
#    x_data = np.arange(start1, stop1, spacing1)
#    y_data = np.arange(start2, stop2, spacing2)
 #   points = {"x": x_data, "y": y_data, "z":np.full((len(x_data),len(y_data)), np.nan)}  # Declaration line
#    def update_fn():
#        global points
 #       if not points["z"].size:
#            dispsq = hv.Image(())
 #       else:
  #          dispsq = hv.Image((points["x"], points["y"], points["z"])).opts(norm=dict(framewise=True))
  #      return dispsq
  #  dmap = hv.DynamicMap(update_fn, streams=[hv.streams.Stream.define("Dummy")()])
  #  hv.ipython.display(dmap)
  #  for i in range(len(x_data)):
  #      for j in range(len(y_data)):
  #      #data.append((i, j, i**2 + j**2))
  #          time.sleep(.1)
  #          #q.put(i**2+j**2)
  #          points['z'][i,j] =points['x'][i]**2+points['y'][j]**2
  #          dmap.event()
  #  return


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

class PlottingThread (threading.Thread):
    def __init__(self, threadID, name, init_val1, end_val1, spacing1, init_val2, end_val2, spacing2):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.init_val1 = init_val1
        self.end_val1 = end_val1
        self.spacing1 = spacing1
        
        self.init_val2 = init_val2
        self.end_val2 = end_val2
        self.spacing2 = spacing2
        
    def run(self):
        print("Starting3 " + self.name)
        img = simulate_measure(self.init_val1, self.end_val1, self.spacing1, self.init_val2, self.end_val2, self.spacing2)
        print ("Exiting " + self.name)
        return img
    
class PlottingThread_inline (threading.Thread):
   
    def __init__(self, threadID, name, point_d, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.point_dict = point_d
        self.qu = q
        self.stopflag = False

        
    def run(self):
        print("Starting3 " + self.name)
        warnings.filterwarnings("ignore", message="All-NaN slice encountered\n drange = (np.nanmin(data), np.nanmax(data))")
        img = simulate_measure_inline(self.point_dict)
        q.put(img)
        print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return
    
def sweep2D(start1, stop1, spacing1, start2, stop2, spacing2):
    plot_thread = PlottingThread(1, "Thread-1", start1, stop1, spacing1, start2, stop2, spacing2)
    img = plot_thread.start()
    return img

q=queue.Queue()

def sweep2D_inline(start1, stop1, spacing1, start2, stop2, spacing2):
    global q
    global plot_thread
    
    #Need to make sure queue is clear if it was never taken from previous sweep
    #clear_queue()
    q = queue.Queue()
    
    x_data = np.arange(start1, stop1, spacing1)
    y_data = np.arange(start2, stop2, spacing2)
    points2 = {"x": x_data, "y": y_data, "z":np.full((len(y_data),len(x_data)), np.nan)}
        #dmap_in = hv.DynamicMap(update_fn_in, streams=[hv.streams.Stream.define("Dummy")()])
        #hv.ipython.display(dmap_in)
        #q = queue.Queue()
    plot_thread = PlottingThread_inline(1, "Thread-1", points2, q)
    img = plot_thread.start()
        #plot_thread.start()
    time.sleep(.1)
    print(plot_thread.isAlive())
        #plot_thread.join()
    return img
    
def get_plot():
    global q
    try:
        return q.get_nowait()
    except queue.Empty:
        print("No Plot to save!")


def abort_sweep():
    global plot_thread
    plot_thread.stopflag = True
    return

    
    