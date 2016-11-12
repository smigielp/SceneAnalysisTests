'''
Class used for test cases for paper in ESWA
'''
from Recognition import ShapeRecognition
from Tools       import ImageProcessor
from Tools       import GnuplotDrawer
from Tools       import ImageApi
from SceneRepTools.Structures import GraphStructure 
import Control






#############################################################################
# Test function used in test case
# @TODO - move to ImageProcessor class as a complete method
#           
def localizeObjects(bigMapPic, smallMapsPic, markedObjectIdx, debugLevel, graphLevel=1): 
    flt = ImageApi.Filter() 
    processor = ImageProcessor.ImageProcessor(Control.PARAMETER_FILE_NAME, bigMapPic['params'], debugLevel) 
    processor2 = ImageProcessor.ImageProcessor(Control.PARAMETER_FILE_NAME, smallMapsPic['params'], debugLevel)   
                       
    bigMap = []
    bigMap.append(flt.loadCvImage(bigMapPic['file'], processor.imgResizeScale))  
    smallMaps = []
    for fileName in smallMapsPic['file']:  
        smallMaps.append(flt.loadCvImage(fileName, processor2.imgResizeScale))
    
    vectorSetBigMap = processor.getVectorizedImageSet(bigMap)
    vectorSetSmallMaps = processor2.getVectorizedImageSet(smallMaps)   
    
    vectorBigMap       = vectorSetBigMap[0]['vect']
    vectorBigMapDomain = vectorSetBigMap[0]['domain']
    
    vectorSmallMap1       = vectorSetSmallMaps[0]['vect']  
    vectorSmallMap1Domain = vectorSetSmallMaps[0]['domain'] 
                     
    bigMapObjGraph = GraphStructure(vectorBigMap, vectorBigMapDomain, graphLevel)
            
    print "Graph:"   
    print bigMapObjGraph.getGraphElement(2)
    
    smallMap1ObjGraph = GraphStructure(vectorSmallMap1, vectorSmallMap1Domain, graphLevel)       
    markedObj = bigMapObjGraph.getGraphElement(markedObjectIdx[0])
    
    objectShapeMatching = ShapeRecognition.findPatternInGraph(markedObj, smallMap1ObjGraph.getGraph())
    
    print ''
    print '=====Matching Result==============================='
    if objectShapeMatching is not None:
        objStats = objectShapeMatching['fullStats']['centeObjMatchStats']
        print 'object: ', objStats['obj']
        print 'center: ', objStats['center']
        print 'idx   : ', objStats['graphIdx']
        print 'scale : ', objStats['scale']
        print 'rotate: ', objStats['rotate']
        print '----Matching neighbors----------------------' 
        nbrStats = objectShapeMatching['fullStats']['neighborMatchStats']
        for stat in nbrStats:
            if stat == -1: 
                print "No match"
            else:
                print "Match rate: ", stat
        
        GnuplotDrawer.printObjectGraph(smallMap1ObjGraph, objectShapeMatching['matched'])
        
    else:
        print 'NO MATCH'   
    print '==================================================='
      
    #GnuplotDrawer.printObjectGraph(bigMapObjGraph)
    objectsToMark = {}
    for idx in markedObjectIdx:
        objectsToMark[idx] = 'all'
    
    GnuplotDrawer.printObjectGraph(bigMapObjGraph, objectsToMark)
    GnuplotDrawer.printObjectGraph(smallMap1ObjGraph)
    
