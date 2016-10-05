'''
Created on 2 kwi 2016

@author: Piter
'''
from VehicleApi import QuadcopterApi 
from dronekit_sitl import SITL
from time import sleep

import Tkinter


sitl = SITL()
sitl.download('copter', '3.3', verbose=True)
sitl_args = ['-I0', '--model', 'quad', '--home=49.9880962,19.90333,584,353']
sitl.launch(sitl_args, await_ready=True, restart=True)


print "Connecting to vehicle on: 'tcp:127.0.0.1:5760'"
vehicle = QuadcopterApi('tcp:127.0.0.1:5760')
print vehicle.quad.capabilities


def onClosing():
    vehicle.close()
    sitl.stop()
    print("Completed")



vehicle.setModeGuided()
vehicle.takeoff(5) 

vehicle.getState()


def onKeyPress(event):
    key = event.keycode
    if(key == 38):
        print "forward"
        vehicle.goto(5, 0)
        vehicle.getState()
    elif(key == 40):
        print "backward"
        vehicle.goto(-5, 0)
        vehicle.getState()
    elif(key == 37):
        print "left"
        vehicle.goto(0, -5)
        vehicle.getState()
    elif(key == 39):
        print "right"
        vehicle.goto(0, 5)
        vehicle.getState()
    elif(key == 81):
        print "fift up"
        vehicle.goto(0, 0, 2, altRelative=True)
        #vehicle.changeAlt(2)
        vehicle.getState()
    elif(key == 65):
        print "go down"        
        vehicle.goto(0, 0, -2, altRelative=True)
        #vehicle.changeAlt(-2)
        vehicle.getState()
    elif(key == 49):
        print "yaw left"
        vehicle.changeHeading(-10, False)
        sleep(1)
        vehicle.getState()
    elif(key == 50):
        print "yaw right"
        vehicle.changeHeading(10, False)
        sleep(1)
        vehicle.getState()


root = Tkinter.Tk()
#root.geometry('300x200')
#text = Tkinter.Text(root, background='black', foreground='white', font=('Comic Sans MS', 12))
#text.pack()
root.bind('<KeyPress>', onKeyPress)
root.protocol("WM_DELETE_WINDOW", onClosing)
root.mainloop()


    