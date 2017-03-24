from threading import Thread

import MovementControlTest
import MovementTracker
from TestCases  import GraphSearchTest, Model3DSpaceTest, SceneModelTest, Model3DTest
from ImageApi import Filter, CameraApi, CameraApi2
from ImageProcessor import ImageProcessor
from time import sleep
from datetime import datetime
from Utils import getCentroid, calcMoveToTargetHorizont, calcHeadingChangeForFrontPhoto
import GnuplotDrawer
import sys

from dronekit_sitl import SITL


DEBUG_LEVEL = 0

PARAMETER_FILE_NAME = "Parameters/algorithms_parameters.txt"


class BaseControl(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.cameraApi = CameraApi2()
        self.filter = Filter()
        self.imgProc = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
        self.stopThread = False
        self.testCasesList = [
                        'Graph partial match',
                        'Graph complete match',
                        'Extended graph partial match',
                        'Real photo graph match',
                        'Blank test'
                        '3D model building',
                        'Vectorization test',
                        'MavLink protocol test',
                        'Mavlink test',
                        'Movement test'
                    ]

    def setTestCase(self, testCase):
        self.testCase = testCase

    def setView(self, viewComponent):
        self.gui = viewComponent


    def run(self):
        while not self.stopThread and self.cameraApi.isOpened():
            self.getLiveCameraView()

    def killApplication(self):
        try:
            self.stopThread = True
            self.cameraApi.stopCapture()
            self.cameraApi.release()
        except:
            print "Error closing VideoCapture."
        sys.exit


    #############################################################################
    # Executes the test case 
    #           
    def executeMainTask(self, testCase):
        print "Running test "+str(testCase)
        # Testing partial match of the scene fragment
        if testCase == 0:
            bigMap = {'file': 'TestPictures/big_map.png', 'params': 'parameters_test1'}
            smallMap = {'file': 'TestPictures/small_map1.png', 'params': 'parameters_test1'}
            GraphSearchTest.localizeObjects(bigMap, smallMap, [5], DEBUG_LEVEL)

        # Testing complete match of the scene fragment
        elif testCase == 1:
            bigMap = {'file': 'TestPictures/big_map.png', 'params': 'parameters_test1'}
            smallMap = {'file': 'TestPictures/small_map_complete.png', 'params': 'parameters_test1'}
            GraphSearchTest.localizeObjects(bigMap, smallMap, [5], DEBUG_LEVEL)

        # Testing partial match in extended graph
        elif testCase == 2:
            bigMap = {'file': 'TestPictures/big_map_double.png', 'params': 'parameters_mid_res2'}
            smallMaps = {'file': ['TestPictures/small_map_complete.png'], 'params': 'parameters_test3'}
            GraphSearchTest.localizeObjects(bigMap, smallMaps, [10, 5], DEBUG_LEVEL, graphLevel=1)

        # Testing match between real photo and the scene graph
        # with construction of 3D representation of found object (also based on real photos)
        elif testCase == 3:
            pictures = [{'file': ['TestPictures/front_test_5.png', 0], 'params': 'parameters_test_5'},
                        {'file': ['TestPictures/right_test_5.png', 0.5], 'params': 'parameters_test_5'},
                        {'file': ['TestPictures/top_test_5.png', None], 'params': 'parameters_test_5'}]
            SceneModelTest.buildSceneModel(pictures, DEBUG_LEVEL)
        elif testCase == 4:
            pictures = [{'file': ['TestPictures/front_test_6.png', 0], 'params': 'parameters_test_6'},
                        {'file': ['TestPictures/right_test_6.png', 0.5], 'params': 'parameters_test_6'},
                        {'file': ['TestPictures/top_test_6.png', None], 'params': 'parameters_test_6'}]
            Model3DTest.loadImagesWithAngles(pictures, DEBUG_LEVEL)

        #Building 3D model
        elif testCase == 5:
            pictures = [{'file': ['TestPictures/b2_right_preproc.png', 0.5], 'params': 'parameters_test1'},
                        {'file': ['TestPictures/b2_front_preproc.png', 0], 'params': 'parameters_test1'},
                        {'file': ['TestPictures/b2_top_preproc.png', None], 'params': 'parameters_test1'}]
            Model3DSpaceTest.loadImagesWithAngles(pictures, DEBUG_LEVEL)

        # Ad-hoc vectorization test
        elif testCase == 6:
            flt = Filter()
            sourceImage = flt.loadCvImage('TestPictures/big_map.png')
            processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
            sourceVectors = processor.getVectorRepresentation(sourceImage, self.filter.prepareImage)
            targetCoords=getCentroid(sourceVectors['vect'][2])
            print sourceVectors['vect']
            print targetCoords
            print "Distance to target: ", calcMoveToTargetHorizont(targetCoords, 10, 90, 30, 60)
            for i in range(len(sourceVectors['vect'])):
                print "Object number ", i, ":"
                calcHeadingChangeForFrontPhoto(sourceVectors['vect'][i], sourceVectors['vect'], 50)
            GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])

        # Test komunikacji po MavLink
        elif testCase == 7:
            print datetime.now(), " - Mavlink test "
            #dron = QuadcopterApi()
            #dron.setModeGuided()
            #dron.setCameraAim(VehicleApi.FRONT)
            #sleep(3)
            #
            #dron.setYaw(180)
            #dron.goto(3, 3)
            #dron.goto_position_relative(4, 0, 0)
            imagecv = self.cameraApi.getFrame()

            image = self.filter.prepareImage(imagecv)
            vectors = self.imgProc.getVectorRepresentation(image, edgesExposed=False)
            GnuplotDrawer.printMultiPointPicture(vectors['vect'], vectors['domain'])

            imagetk = self.filter.getImageTk(image, self.gui.IMAGE_WIDTH)
            self.gui.showTakenCameraImg(imagetk)
            sleep(0.5)
        elif testCase == 8:
            print "Testing movement control"
            MovementControlTest.runTest()
            return

    def processOpenedFile(self, filename):
        imagecv = self.filter.loadCvImage(filename)
        # some processing...        
        imagetk = self.filter.getImageTkBGR(imagecv, self.gui.IMAGE_WIDTH)
        self.gui.showOpenedImg(imagetk)


    def getCameraFrame(self):
        imagecv = self.cameraApi.getFrame()
        # some processing...
        imagetk = self.filter.getImageTk(imagecv, self.gui.IMAGE_WIDTH)
        self.gui.showTakenCameraImg(imagetk)
        sleep(1)


    def getLiveCameraView(self):
        imagecv = self.cameraApi.getFrame()
        # some processing...
        imagetk = self.filter.getImageTkBGR(imagecv, self.gui.IMAGE_WIDTH)
        self.gui.showLiveCameraImg(imagetk)

