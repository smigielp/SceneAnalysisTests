from threading import Thread

from TestCases import GraphSearchTest, Model3DSpaceTest, SceneModelTest, Model3DTest, MovementControlTest, UAVTest, PhdTests
from ImageApi import Filter, CameraApi, CameraApi2
from ImageProcessor import ImageProcessor
from time import sleep
from datetime import datetime
from Utils import getCentroid, calcMoveToTargetHorizont, calcHeadingChangeForFrontPhoto
#from Recognition import FuzzyShapeRecognition
import ImageApi
import GnuplotDrawer
import FuzzyShapeRecognition
import ShapeRecognition
import sys
import math

from dronekit_sitl import SITL


DEBUG_LEVEL = 3

PARAMETER_FILE_NAME = "../../Parameters/algorithms_parameters.txt"


class BaseControl(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.cameraApi = CameraApi2()
        self.filter = Filter()
        self.imgProc = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
        self.stopThread = False
        self.testCasesList = [
                        'Graph partial match', #0
                        'Graph complete match', #1
                        'Extended graph partial match', #2
                        'Real photo recognition test', #3
                        'Fuzzy recognition', #4
                        '3D model building', #5
                        'Vectorization test', #6
                        'Mavlink test', #7
                        'Movement test', #8
                        'PHD Tests - big scene', #9
                        'PHD Tests - small scene', #10
                        'Ad hoc test' #11
                    ]

    def setTestCase(self, testCase):
        self.testCase = testCase


    def setView(self, viewComponent):
        self.gui = viewComponent


    def run(self):
        pass
        # Executing UAVTest
        # self.executeMainTask(9) 
        

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
        
        # Fuzzy Recognition
        elif testCase == 4: 
            processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1', inDebugLevel=DEBUG_LEVEL)
            imagecv = self.filter.loadCvImage("E:\Programowanie\workspace\SceneAnalysisTests\TestPictures\\a_complex.png")
            sourceVectors = processor.getVectorRepresentation(imagecv, self.filter.imagePreprocess, self.filter.imageEdgeDetect)

            #sourceVectors = {'color': [[235, 235, 235]], 'vect': [[[181.5, 250.0], [182, 311], [184, 307], [329, 311], [485, 311], [507, 306], [507, 242], [503, 226], [192, 223], [182, 234], [181.5, 250.0]]], 'domain': [[0, 720L], [0, 480L]]}

            image = self.filter.loadCvImage("E:\Programowanie\workspace\SceneAnalysisTests\TestPictures\\b_complex.png")
            searchedObjectVectors = processor.getVectorRepresentation(image, self.filter.imagePreprocess, self.filter.imageEdgeDetect)

            print searchedObjectVectors['vect'][0]

            found = FuzzyShapeRecognition.findSinglePattern(searchedObjectVectors['vect'][0], sourceVectors['vect'])
            print found
            
        # Building 3D model
        elif testCase == 5:
            pictures = [{'file': ['TestPictures/ImageScanSide.jpg', 0.5], 'params': 'parameters_test2'},
                        {'file': ['TestPictures/ImageScanFront.jpg', 0], 'params': 'parameters_test2'},
                        {'file': ['TestPictures/ImageForScanAbove.jpg', None], 'params': 'parameters_test2'}]
            Model3DSpaceTest.loadImagesWithAngles(pictures, DEBUG_LEVEL)

        # Ad-hoc vectorization test
        elif testCase == 6:
            flt = Filter()
            sourceImage = flt.loadCvImage('E:\NAUKA\Doktorat\Do rozprawy\obrazy_mainapp\big_map.png')
            processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
            sourceVectors = processor.getVectorRepresentation(sourceImage, self.filter.imagePreprocess, self.filter.imageEdgeDetect)
            targetCoords=getCentroid(sourceVectors['vect'][2])
            print sourceVectors['vect']
            print targetCoords
            print "Distance to target: ", calcMoveToTargetHorizont(targetCoords, 10, 90, 30, 60)
            for i, vert in enumerate(sourceVectors['vect']):
                print "Object number ", i, ":"
                ret = calcHeadingChangeForFrontPhoto(vert, sourceVectors['vect'], 10, 3, 90, 90)
                if ret[0]!=[-1,-1]:
                    if ret[1]:
                        sourceVectors['vect'].append([ret[0], [ret[0][0]+50, ret[0][1] + 50 * math.tan(math.radians(90-ret[1]))]])
                    else:
                        sourceVectors['vect'].append([ret[0], [ret[0][0], ret[0][1]+50]])
                    if ret[3]:
                        sourceVectors['vect'].append([ret[2], [ret[2][0]+50, ret[2][1] + 50 * math.tan(math.radians(180 - ret[1]))]])
                    else:
                        sourceVectors['vect'].append([ret[2], [ret[2][0], ret[2][1]+50]])
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
            #self.gui.showTakenCameraImg(imagetk)
            sleep(0.5)
            
        elif testCase == 8:
            print "Testing movement control"
            #MovementControlTest.runTest(sitlTest=True)
            MovementControlTest.runRecMovementTest(sitlTest=True)
            return
        
        elif testCase == 9:
            PhdTests.runTest()
            return

        elif testCase == 10:
            PhdTests.runTest()
            return
        
        elif testCase == 11:
            f = Filter()
            img = f.loadCvImage("TestPictures/b_complex.png")
            processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1')
            searchedObject = processor.getVectorRepresentation(img, f.imagePreprocess, f.imageEdgeDetect, ImageApi.RED)
            GnuplotDrawer.printVectorPicture(searchedObject['vect'], searchedObject['domain'])
            print searchedObject
        


    def processOpenedFile(self, filename):
        imagecv = self.filter.loadCvImage(filename)
        processor = ImageProcessor(PARAMETER_FILE_NAME, 'parameters_test1', inDebugLevel=DEBUG_LEVEL)        
        sourceVectors = processor.getVectorRepresentation(imagecv, self.filter.imagePreprocess, self.filter.imageEdgeDetect)
        GnuplotDrawer.printVectorPicture(sourceVectors['vect'], sourceVectors['domain'])
        print "VECTORS: "
        print sourceVectors

        #print ShapeRecognition.extractPattern(sourceVectors['vect'][0], 1.0)

        #imagetk = self.filter.getImageTkBGR(imagecv, self.gui.IMAGE_WIDTH)
        #self.gui.showOpenedImg(imagetk)


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

    def showImage(self, imagecv):
        imagetk = self.filter.getImageTk(imagecv, self.gui.IMAGE_WIDTH)
        self.gui.showTakenCameraImg(imagetk)