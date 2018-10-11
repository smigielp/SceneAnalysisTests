from Recognition import GraphRecognition
from Tools       import ImageProcessor
from Tools       import GnuplotDrawer
from Tools       import ImageApi
from SceneRepTools.Structures import GraphStructure 
import Control

       
def runTest(debugLevel=1, graphLevel=1): 
    #vectorBigMap = [[[181.0, 249.0], [165, 271], [184, 290], [215, 254], [219, 244], [199, 228], [181.0, 249.0]], [[243.0, 437.0], [253, 436], [260, 426], [267, 427], [308, 413], [313, 404], [305, 379], [301, 378], [256, 400], [251, 395], [242, 370], [229, 370], [222, 374], [217, 384], [220, 400], [233, 432], [243.0, 437.0]], [[284.0, 106.5], [297, 111], [304, 106], [317, 67], [318, 55], [247, 31], [238, 43], [236, 59], [247, 68], [277, 78], [280, 81], [278, 94], [284.0, 106.5]], [[382.5, 326.0], [384, 348], [395, 360], [398, 404], [406, 412], [425, 410], [429, 406], [426, 357], [430, 352], [441, 348], [439, 321], [435, 318], [390, 321], [382.5, 326.0]], [[484.5, 174.5], [480, 190], [484, 198], [525, 209], [536, 206], [553, 109], [553, 102], [549, 98], [508, 86], [499, 90], [495, 114], [499, 119], [512, 122], [517, 128], [516, 143], [512, 148], [512, 167], [507, 171], [489, 168], [484.5, 174.5]]]
    vectorBigMap = [[[181.0, 249.0], [165, 271], [184, 290], [215, 254], [219, 244], [199, 228], [181.0, 249.0]], [[243.0, 437.0], [253, 436], [260, 426], [267, 427], [308, 413], [313, 404], [305, 379], [301, 378], [256, 396], [251, 395], [242, 370], [229, 370], [222, 374], [217, 384], [220, 400], [233, 432], [243.0, 437.0]], [[284.0, 106.5], [297, 111], [304, 106], [317, 67], [318, 55], [247, 31], [238, 43], [236, 59], [247, 68], [277, 78], [280, 81], [278, 94], [284.0, 106.5]], [[382.5, 326.0], [384, 348], [395, 360], [398, 404], [406, 412], [425, 410], [429, 406], [426, 357], [430, 352], [441, 348], [439, 321], [435, 318], [390, 321], [382.5, 326.0]], [[484.5, 174.5], [480, 190], [484, 198], [525, 209], [536, 206], [553, 109], [553, 102], [549, 98], [508, 86], [499, 90], [495, 114], [499, 119], [512, 122], [517, 128], [516, 143], [512, 148], [512, 167], [507, 171], [489, 168], [484.5, 174.5]]]
    vectorBigMapDomain = [[0, 720], [0, 576]]
    bigMapObjGraph = GraphStructure(vectorBigMap, vectorBigMapDomain, graphLevel)
                
    vectorsSmallMap = [[[71.0, 260.5], [71, 266], [119, 333], [118, 336], [102, 347], [101, 351], [129, 388], [133, 387], [200, 338], [200, 334], [175, 299], [172, 299], [164, 305], [158, 305], [109, 236], [107, 236], [71.0, 260.5]], [[260.5, 210.0], [310, 148], [314, 149], [344, 174], [371, 142], [371, 140], [362, 131], [303, 81], [298, 85], [222, 175], [222, 177], [252, 206], [258, 211], [260.5, 210.0]], [[478.5, 231.0], [461, 318], [466, 321], [508, 329], [510, 327], [526, 237], [490, 229], [481, 229], [478.5, 231.0]]]
    vectorsSmallMapDomain = [[0, 584], [0, 467]]
    smallMapObjGraph = GraphStructure(vectorsSmallMap, vectorsSmallMapDomain, graphLevel)  
         
    markedObjectIdx = 1
    markedObj = smallMapObjGraph.getGraphElement(markedObjectIdx)
    
    searchResults = GraphRecognition.findPatternInGraph(markedObj, bigMapObjGraph.getGraph())
    
    print ''
    print '=====Matching Result==============================='
    if len(searchResults) > 0:
        # getting best matching 
        objectShapeMatching = searchResults[0]
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
        
        GnuplotDrawer.printObjectGraph(bigMapObjGraph, objectShapeMatching['matched'])        
    else:
        print 'NO MATCH'   
        GnuplotDrawer.printObjectGraph(bigMapObjGraph)
    print '==================================================='
           
    objectsToMark = {markedObjectIdx: 'all'}
        
    GnuplotDrawer.printObjectGraph(smallMapObjGraph, objectsToMark)
    
    
