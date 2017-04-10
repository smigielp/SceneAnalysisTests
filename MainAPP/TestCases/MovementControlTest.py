'''
Created on 1 mar 2017

@author: Mateusz Raczynski
'''
from time import sleep

import numpy as np

import MovementTracker
import VehicleApi
import Visualizer
from CommandQueue import CommandQueue
from VehicleApi import QuadcopterApi, Thread
from dronekit_sitl import SITL

import Tkinter

vehicle = None
sitl = None
root = None
modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
modeCamera = VehicleApi.FRONT


def _forward(event):
    if vehicle is None:
        return
    print '_forward called'
    vehicle.commandQueue.moveForward(1)


def _back(event):
    if vehicle is None:
        return
    print '_back called'
    vehicle.commandQueue.moveForward(-1)


def _left(event):
    if vehicle is None:
        return
    print '_left called'
    vehicle.commandQueue.moveToLocRelativeHeading(0, -1)


def _right(event):
    if vehicle is None:
        return
    print '_right called'
    vehicle.commandQueue.moveToLocRelativeHeading(0, 1)


def _rotateLeft(event):
    if vehicle is None:
        return
    print '_rotateLeft called'
    vehicle.commandQueue.changeHeading(-10)


def _rotateRight(event):
    if vehicle is None:
        return
    print '_rotateRight called'
    vehicle.commandQueue.changeHeading(10)


def _increaseHeight(event):
    if vehicle is None:
        return
    print '_increaseHeight called'
    vehicle.commandQueue.goto(0, 0, 2, True)


def _decreaseHeight(event):
    if vehicle is None:
        return
    print '_decreaseHeight called'
    vehicle.commandQueue.goto(0, 0, -2, True)


def _confirmQueue(event):
    if vehicle is None:
        return
    print '_confirmQueue called'
    vehicle.commandQueue.confirm()


def _return(event):
    if vehicle is None:
        return
    print '_return called'
    dvec = np.array([0, 0, 4]) - vehicle.getPositionVector()
    vehicle.goto(dvec[1], dvec[0], dvec[2], True)


def _switchCameraPos(event):
    if vehicle is None:
        return
    print '_switchCameraPos called'
    global modeCamera
    if modeCamera == VehicleApi.FRONT:
        vehicle.setCameraAim(VehicleApi.DOWN)
        modeCamera = VehicleApi.DOWN
    elif modeCamera == VehicleApi.DOWN:
        vehicle.setCameraAim(VehicleApi.FRONT)
        modeCamera = VehicleApi.FRONT
    print vehicle.quad.gimbal


def _switchMode(event):
    if vehicle is None:
        return
    global modeQueue
    print '_switchMode called'
    if (modeQueue == CommandQueue.Mode.QUEUE_COMMANDS):
        print 'Switching mode to IMM_EXECUTE'
        modeQueue = CommandQueue.Mode.IMM_EXECUTE
    else:
        print 'Switching mode to QUEUE_COMMANDS'
        modeQueue = CommandQueue.Mode.QUEUE_COMMANDS
    vehicle.commandQueue.setMode(modeQueue)


def _setGuidedMode(event):
    vehicle.setMode('GUIDED')

  
    
def _onClosing():
    MovementTracker.stop()
    root.destroy()
    while vehicle is None:
        sleep(0.5)
    vehicle.close()
    if sitl is not None:
        sitl.stop()
    print("Completed")


def createVehicle(sitlTest = True):
    global vehicle
    if sitlTest:
        global sitl
        sitl = SITL()
        sitl.download('copter', '3.3', verbose=True)
        sitl_args = ['-I0', '--model', 'quad', '--home=49.9880962,19.90333,584,353']
        sitl.launch(sitl_args, await_ready=True, restart=True)
        print "Connecting to vehicle on: 'tcp:127.0.0.1:5760'"
        vehicle = QuadcopterApi('tcp:127.0.0.1:5760')
        vehicle.setMode('GUIDED')
        vehicle.arm()
        vehicle.takeoff(5)
        vehicle.getState()
    else:
        print "Connecting to vehicle on: '127.0.0.1:14550'"
        vehicle = QuadcopterApi('127.0.0.1:14550')
    vehicle.commandQueue.shouldMakeAdjustment(True)
    MovementTracker.start(vehicle)


def createGUI():
    thread = Thread(name='ControlPanelThread')
    thread.run = _createGUI
    thread.start()

manual = """
a - go left
d - go right
w - go forward
s - go back
q - rotate left
e - rotate right
t - return to [0,0,4]
c - switch camera position
left control - decrease height
space - increase height
enter - confirm command queue
r - switch command queue mode
m - set mode of vehicle to Guided
"""

def _createGUI():
    global root
    root = Tkinter.Tk()
    root.bind('a', _left)
    root.bind('d', _right)
    root.bind('w', _forward)
    root.bind('s', _back)
    root.bind('q', _rotateLeft)
    root.bind('e', _rotateRight)
    root.bind('t', _return)
    root.bind('c', _switchCameraPos)
    root.bind('<Control_L>', _decreaseHeight)
    root.bind('<space>', _increaseHeight)
    root.bind('<Return>', _confirmQueue)
    root.bind('r', _switchMode)
    root.bind('m', _setGuidedMode)
    root.protocol("WM_DELETE_WINDOW", _onClosing)
    text = Tkinter.Text(root)
    text.insert(Tkinter.INSERT,manual)
    text.tag_configure("center", justify='center')
    text.tag_add("center", 1.0, "end")

    text.config(state=Tkinter.DISABLED)
    text.pack()
    root.mainloop()


def runTest(sitlTest):
    createGUI()
    createVehicle(sitlTest)
    veh = vehicle

    window = Visualizer.createWindow(veh)
    window.cameraC.moveFRU(f=-2)

def runRecMovementTest(sitlTest):
    #todo: make it work with real drone
    ###################
    # createGUI() and vehicle
    createVehicle(sitlTest)
    veh = vehicle
    window = Visualizer.createWindow(veh)
    if not isinstance(veh,VehicleApi.QuadcopterApi):
        return
    window.cameraFromVehicle(True)

    ###################
    # raise heigh enough
    veh.commandQueue.goto(0.,0.,10,True)
    veh.commandQueue.changeHeading(120,False)
    veh.commandQueue.confirm()

    ###################
    # make a photo
    veh.setCameraAim(VehicleApi.DOWN)
    import math
    window.cameraC.lookAtEulerExt(x=math.radians(-90))
    sleep(0.5)
    photo = window.grabFrame()

    controlPoint = window.obtainModelObject()
    pos =Visualizer.tENUtoXYZ(veh.getPositionVector())
    print "Making photo at: ",pos
    controlPoint.data = [pos]
    controlPoint.color = np.array([0.,0.,1.])
    controlPoint.render = True

    photoDirection = veh.quad.heading
    import ImageApi
    img = ImageApi.PILimageFromArray(photo,window.getWindowSize(),"RGBA",True)
    ##img.show()
    #img.save("image_test.jpg")
    rawImage = ImageApi.PILImageToCV(img)

    ###################
    # parse photo
    from ImageProcessor import ImageProcessor
    from Control import PARAMETER_FILE_NAME
    from Utils import getCentroid
    from Utils import calcMoveToTargetHorizont
    from Utils import calcHeadingChangeForFrontPhoto
    import GnuplotDrawer
    flt = ImageApi.Filter()
    processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
    sourceVectors = processor.getVectorRepresentation(rawImage, flt.prepareImage)
    objectIndex = 0
    if len(sourceVectors['vect'])<objectIndex+1:
        print "VECTOR REPRESENTATION HAS INVALID AMOUNT OF OBJECTS ... RETURNING"
        veh.setCameraAim(VehicleApi.FRONT)
        window.cameraC.lookAtEulerExt(x=0)
        return
    targetCoords = getCentroid(sourceVectors['vect'][objectIndex])
    print sourceVectors['vect']
    print targetCoords
    print "Recognized objects: ",len(sourceVectors['vect'])
    print "Object number ", objectIndex, ":"
    result = calcHeadingChangeForFrontPhoto(sourceVectors['vect'][objectIndex], sourceVectors['vect'], 90)
    if result is None:
        print "calcHeadingChangeForFrontPhoto RETURNED NONE ... RETURNING"
        veh.setCameraAim(VehicleApi.FRONT)
        window.cameraC.lookAtEulerExt(x=0)
        return
    photoPoint, headingChange, chosenEdge = result
    GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])

    ###################
    #reset camera
    veh.setCameraAim(VehicleApi.FRONT)
    window.cameraC.lookAtEulerExt(x=0)

    ###################
    #calc dpos
    alt = 20
    imgWidth = window.getWindowSize()[0]
    imgHeight = window.getWindowSize()[1]
    fovH = window.cameraC.fieldOfView
    fovV = fovH*1./window.cameraC.aspect
    dposToTarget = calcMoveToTargetHorizont(targetCoords, alt, photoDirection, fovV, fovH,resolutionX=imgWidth,resolutionY=imgHeight)
    dposToPhotoPoint = calcMoveToTargetHorizont(photoPoint, alt, photoDirection, fovV, fovH,resolutionX=imgWidth,resolutionY=imgHeight)
    print "Distance to target: ", dposToTarget
    print "Distance to photoPoint: ", dposToPhotoPoint

    ###################
    #move to calculated position
    print "Moving by: ",dposToPhotoPoint[0],dposToPhotoPoint[1]
    print "Height: ",2
    print "Heading: ",photoDirection+float(headingChange)
    veh.commandQueue.moveToLocRelativeHeading(dposToPhotoPoint[0],dposToPhotoPoint[1])
    veh.commandQueue.goto(0.,0.,2,False)
    #veh.commandQueue.goto(dposToPhotoPoint[0],dposToPhotoPoint[1],2,False) # <-------
    veh.commandQueue.changeHeading(photoDirection+float(headingChange),False)
    veh.commandQueue.confirm()

    ###################
    #make a photo again

    ###################
    #save it for building 3d model


if __name__ == "__main__":
    runTest(False)
