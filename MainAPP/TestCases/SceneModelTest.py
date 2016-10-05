from Tools   import ImageProcessor
from Tools   import GnuplotDrawer
from Tools   import ImageApi

import Control




def buildSceneModel(filesList, debugLevel):
    flt = ImageApi.Filter() 
    processor = ImageProcessor.ImageProcessor(debugLevel)
    imageSet = []
    for i, fileSpec in enumerate(filesList):
        if i == 1:
            processor.setAlgorithmsParameters(Control.PARAMETER_FILE_NAME, fileSpec['params'])
            image = flt.loadFile(fileSpec['file'][0], processor.imgResizeScale)
            photoAngle = fileSpec['file'][1]
            vectorImage = processor.getVectorRepresentation(image)
            GnuplotDrawer.printVectorPicture(vectorImage['vect'], vectorImage['domain'])
            imageSet.append([vectorImage['vect'], photoAngle])  
    model3D = processor.create3DStructureFromVectors(imageSet) 
    model3D.showAll3D()
   

