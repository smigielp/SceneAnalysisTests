from Tools import ImageProcessor, ImageApi
import Control



#############################################################################
# Loads pictures given in the list. Each picture taken from different side
# of an object
# @filesList['file': pairs of [filename, angle_of_picture]
#                    angle_of_picture:
#                    None - picture taken from the top ("top" picture)
#                    0    - picture taken from the front side of the object ("front" picture)      
#                    0.5  - picture taken from the right side of the object ("right" picture)
def loadImagesWithAngles(filesList, debugLevel):
    flt = ImageApi.Filter() 
    processor = ImageProcessor.ImageProcessor(debugLevel)
    imageSet = []
    for fileSpec in filesList:
        processor.setAlgorithmsParameters(Control.PARAMETER_FILE_NAME, fileSpec['params'])
        image = flt.loadFile(fileSpec['file'][0], processor.imgResizeScale)
        photoAngle = fileSpec['file'][1]
        #vectorImage = processor.getVectorRepresentation(image)
        #imageSet.append([vectorImage['vect'], photoAngle])  
        imageSet.append([image, photoAngle])  
    model3D = processor.create3DStructureFromPictures(imageSet) 
    model3D.showAll3D()
    #return imageSet           

