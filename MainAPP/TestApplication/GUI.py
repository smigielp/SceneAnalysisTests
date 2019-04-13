from Control import BaseControl
from Tkinter import *
from threading import Thread
from tkFileDialog import askopenfilename
from ImageApi import Filter
from Tools import GnuplotDrawer


class GUI(Thread):
   
    def __init__(self, controller):
        self.IMAGE_WIDTH = 500
        self.IMAGE_HEIGHT = 400
        self.SMALL_IMAGE_WIDTH = 250
        self.SMALL_IMAGE_HEIGHT = 230        
       
        Thread.__init__(self)
        self.root = Tk()
        self.root.title('Image Processing')  
        self.root.geometry('1350x650+5+5')
        self.root.protocol("WM_DELETE_WINDOW", self.onClosing)

        self.filter = Filter()
        
        self.imageBox = {}
        self.image = {}
        
        liveFrame   = Frame(master=self.root, bd=2, relief=SUNKEN, padx=5, pady=5)
        openedFrame = Frame(master=self.root, bd=2, relief=SUNKEN, padx=5, pady=5)
        takenFrame  = Frame(master=self.root, bd=2, relief=SUNKEN, padx=5, pady=5)
        liveFrame.grid(row=0, column=0)
        takenFrame.grid(row=0, column=1)
        openedFrame.grid(row=0, column=2)
        
        self.imageBox["live"  ] = Canvas(master=liveFrame, width=self.IMAGE_WIDTH, height=self.IMAGE_HEIGHT)   
        self.imageBox["live"  ].pack() 
        self.imageBox["taken" ] = Canvas(master=takenFrame, width=self.IMAGE_WIDTH, height=self.IMAGE_HEIGHT)
        self.imageBox["taken" ].pack()   
        self.imageBox["opened"] = Canvas(master=openedFrame, width=self.SMALL_IMAGE_WIDTH, height=self.SMALL_IMAGE_HEIGHT)    
        self.imageBox["opened"].pack()
        
        self.funcButtonFrame = Label(master=self.root, bd=2, relief=SUNKEN, width=self.IMAGE_WIDTH)        
        self.funcButtonFrame.grid(row=1, column=0)
        self.openFileBtn = Button(self.funcButtonFrame, text="open file", command=self.openFile, padx=10, width=20)
        self.getCameraFrameBtn = Button(self.funcButtonFrame, text="get camera frame", command=self.getCameraFrame, padx=10, width=20)
        self.openFileBtn.grid(row=0)
        self.getCameraFrameBtn.grid(row=1)
        
        self.testCase = IntVar()
        self.radioFrame = Label(master=self.funcButtonFrame, bd=2)
        self.radioFrame.grid(row=2, column=0)
        self.radioButtons = []
        for i in range(len(controller.testCasesList)):
            rb = Radiobutton(self.radioFrame, indicatoron=0, text=controller.testCasesList[i], variable=self.testCase, value=i, width=20, padx=10)
            rb.grid(row=i%5, column=i/5)
            self.radioButtons.append(rb)
            
        self.runTestBtn = Button(self.funcButtonFrame, text="run test", command=self.executeTask, padx=10)
        self.runTestBtn.grid(row=1, column=2)
        
        controller.setView(self)        
        self.control = controller        
        self.start()
    
    
    def onClosing(self):
        self.control.killApplication()
        self.root.destroy()
        GnuplotDrawer.gnuPlots = None

    
    def showTakenCameraImg(self, img):
        self.image["taken"] = img #self.filter.getImageTk(img, IMAGE_WIDTH)
        self.imageBox["taken"].create_image(0, 0, image=self.image["taken"], anchor=NW)

     
    def showOpenedImg(self, img):
        self.image["opened"] = img #self.filter.getImageTk(img, IMAGE_WIDTH)
        self.imageBox["opened"].create_image(0, 0, image=self.image["opened"], anchor=NW) 
        
        
    def showLiveCameraImg(self, img):
        self.image["live"] = img #self.filter.getImageTk(img, IMAGE_WIDTH)
        self.imageBox["live"].create_image(0, 0, image=self.image["live"], anchor=NW)
    
    
    def openFile(self):
        filename = askopenfilename()
        self.control.processOpenedFile(filename)
    
    
    def getCameraFrame(self):
        self.control.getCameraFrame()
    
    
    def executeTask(self):
        self.control.executeMainTask(self.testCase.get())  
        
        
    def run(self):   
        self.root.mainloop()
        

if __name__ == "__main__":
    #root.geometry('250x150+300+300')
    controller = BaseControl()
    view = GUI(controller)    
    controller.start()
    #controller.executeMainTask(1)
    
    