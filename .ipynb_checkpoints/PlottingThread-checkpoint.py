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
        return
    
    def save2D(result, channel1, start1, stop1, channel2, start2,stop2):
        curr_state =qd._convertDF()
        ch1 = qd._parseChannel(channel1)[0]
        ch2 = qd._parseChannel(channel2)[0]

        curr_state.loc['Channel %s' % (ch1,), 'Voltage'] = '%s to %s' % (start1, stop1) 
        curr_state.loc['Channel %s' % (ch2,), 'Voltage'] = '%s to %s' % (start2, stop2)
        result = 1

        return savedData(result, curr_state)

    def save2D(result, channel1, start1, stop1):
        curr_state =qd._convertDF()
        ch1 = qd._parseChannel(channel1)[0]

        #b.loc['Channel %s' % (ch1,), 'Channel Name'] = 'Small Dot Gate'
        curr_state.loc['Channel %s' % (ch1,), 'Voltage'] = '%s to %s' % (start1, stop1) 

        result = 1

        return savedData(result, curr_state)
    
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

            if self.last_thread:
                print(self.last_thread)
                self.last_thread.join()
            print('here3')
            for i in range(len(x_data)):
                for j in range(len(y_data)):
                    if self.stopflag:
                        try:
                            img = list(dmap_in.data.items())[0][1] #This gets the hv.Image object from a Dynamic Map
                            #save
                            return img
                        except IndexError:
                            return
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
            #save
            return img
        
    def run(self):
   
        print("Starting3 " + self.name)
        #time.sleep(.1)
        warnings.filterwarnings("ignore", message="All-NaN slice encountered\n drange = (np.nanmin(data), np.nanmax(data))")
        img = self.simulate_measure_inline()
        if img:
            self.qu.put(img)
        print ("Exiting " + self.name)
        return img
    
    def stop(self):
        return