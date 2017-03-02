'''
Created on 1 mar 2017

@author: Mateusz Raczynski
'''
import MovementTracker
from CommandQueue import CommandQueue
from VehicleApi import QuadcopterApi
from dronekit_sitl import SITL

import Tkinter

vehicle = None
sitl = None
root = None
modeQueue = CommandQueue.Mode.QUEUE_COMMANDS

def _forward(event):
    print '_forward called'
    vehicle.commandQueue.moveForward(1)

def _back(event):
    print '_back called'
    vehicle.commandQueue.moveForward(-1)

def _left(event):
    print '_left called'
    vehicle.commandQueue.moveToLocRelativeHeading(0,-1)

def _right(event):
    print '_right called'
    vehicle.commandQueue.moveToLocRelativeHeading(0,1)

def _rotateLeft(event):
    print '_rotateLeft called'
    vehicle.commandQueue.changeHeading(-10)

def _rotateRight(event):
    print '_rotateRight called'
    vehicle.commandQueue.changeHeading(10)

def _increaseHeight(event):
    print '_increaseHeight called'
    vehicle.commandQueue.goto(0, 0, 2, True)

def _decreaseHeight(event):
    print '_decreaseHeight called'
    vehicle.commandQueue.goto(0,0,-2,True)

def _confirmQueue(event):
    print '_confirmQueue called'
    vehicle.commandQueue.confirm()

def _switchMode(event):
    global modeQueue
    print '_switchMode called'
    if(modeQueue == CommandQueue.Mode.QUEUE_COMMANDS):
        print 'Switching mode to IMM_EXECUTE'
        modeQueue = CommandQueue.Mode.IMM_EXECUTE
    else:
        print 'Switching mode to QUEUE_COMMANDS'
        modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
    vehicle.commandQueue.setMode(modeQueue)

def _onClosing():
    MovementTracker.stop()
    root.destroy()
    vehicle.close()
    sitl.stop()
    print("Completed")

def createVehicle():
    global vehicle
    global sitl
    sitl = SITL()
    sitl.download('copter', '3.3', verbose=True)
    sitl_args = ['-I0', '--model', 'quad', '--home=49.9880962,19.90333,584,353']
    sitl.launch(sitl_args, await_ready=True, restart=True)

    print "Connecting to vehicle on: 'tcp:127.0.0.1:5760'"
    vehicle = QuadcopterApi('tcp:127.0.0.1:5760')
    print vehicle.quad.capabilities

    MovementTracker.start(vehicle)
    vehicle.setModeGuided()
    vehicle.takeoff(5)

    vehicle.getState()

def createGUI():
    global root
    root = Tkinter.Tk()
    #root.bind('<KeyPress>', onKeyPress)
    root.bind('a', _left)
    root.bind('d', _right)
    root.bind('w', _forward)
    root.bind('s', _back)
    root.bind('q', _rotateLeft)
    root.bind('e', _rotateRight)
    root.bind('<Control_L>', _decreaseHeight)
    root.bind('<space>', _increaseHeight)
    root.bind('<Return>', _confirmQueue)
    root.bind('r', _switchMode)
    root.protocol("WM_DELETE_WINDOW", _onClosing)
    root.mainloop()


if __name__ == "__main__":
    createVehicle()
    createGUI()




