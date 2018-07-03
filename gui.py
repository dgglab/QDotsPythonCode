import tkinter as tk

class GUI(threading.Thread):
    #Tkinter class for background updating of instrument values
    request_queue = queue.Queue()
    result_queue = queue.Queue()
    
    def __init__(self):
        threading.Thread.__init__(self)
        
    def submit_to_tkinter(self,loc, value):
        self.request_queue.put((loc, value))
        #return result_queue.get()
        
    def update_name(self, loc, name):
        """Name goes in column 1, with row = channel #"""
        self.request_queue.put((loc, name))

    t = None
    label_dict ={}
    def run(self):
        #global t

        def timertick():
            try: 
                loc, value = self.request_queue.get_nowait()
                
                #display_label = self.label_dict[loc[0]][loc[1]]
                #display_label.config(text='%s' % (value,))
            except queue.Empty:
                pass
            else:

                display_label = self.label_dict[loc[0]][loc[1]]
                display_label.config(text='%s' % (value,))
            
            #Wait 10ms then run timertick again 
            self.t.after(10, timertick)

        self.t = tk.Tk()
        self.t.configure(width=640, height=480, background ='black')
        
        #Set Headers
        tk.Label(self.t, text = 'Channel #', font = ('Calibri',10, 'bold'),bg='white', borderwidth = 0, width=10).grid(row=0, column=0, padx =1, pady=1)
        tk.Label(self.t, text = 'Name', font = ('Calibri',10, 'bold'), bg='white', borderwidth = 0, width=10).grid(row=0, column =1,padx =1, pady=1)
        tk.Label(self.t, text = 'Voltage',font = ('Calibri',10, 'bold'),bg='white', borderwidth = 0, width=10).grid(row=0, column=2, padx =1, pady=1)   
        
        for i in range(1,49):
            label_list = []
            for j in range(3):
                if j == 0:
                    tklabel = tk.Label(self.t, text='Channel %s' % (i,), font = ('Calibri',10), bg='white', borderwidth = 0, width=10 )
                else:
                    tklabel = tk.Label(self.t,text='', font = ('Calibri',10),bg='white', borderwidth = 0, width = 10)
                tklabel.grid(row=i, column=j, padx =1, pady=1)
                #print(tklabel)
                label_list.append(tklabel)
                
            self.label_dict[i] = label_list
        #b = tk.Button(text='test', name='button', command=exit)
        #b.place(x=0, y=0)
        timertick()
        self.t.mainloop()