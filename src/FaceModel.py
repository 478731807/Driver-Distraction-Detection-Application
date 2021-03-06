'''
Mentor - Mr.Prashant Kaushik 
Author - Hrishikesh Singh & Shivan Trivedi
'''

# Import Libraries
import time, math, cProfile, numpy, cv2, subprocess
import cv2 as cv
from collections import deque
from PIL import Image , ImageOps , ImageEnhance
from scipy.cluster import vq
import matplotlib
import matplotlib.pyplot as plt

# Constants
CAMERA_INDEX = 0
SCALE_FACTOR = 20  # video size will be 1/SCALE_FACTOR
FACE_CLASSIFIER_PATH = "classifiers/haar-face.xml"
EYE_CLASSIFIER_PATH = "classifiers/haar-eyes.xml"
FACE_MIN_SIZE = 0.2
EYE_MIN_SIZE = 0.03

DISPLAY_SCALE = 0.3333
FACE_SCALE = 0.25
EYE_SCALE = 0.33333



class FaceModel:
    """
	FaceModel integrates data from the new frame into a model that keeps track of where the eyes are. To do this it uses:
		- A moving average of the most recent frames
		- Facial geometry to fill in missing data
	The resulting model generates a set of two specific regions of interest (ROI's) where blinking is expected to take place.
	"""

    # TODO flush eye history whenever faceRect midpoint changes
    # TODO flush eye history whenever eye rectangle outside of faceRect bbox
    # TODO make sure that eye rectangles don't overlap

    QUEUE_MAXLEN = 50

    QUALITY_QUEUE_MAXLEN = 30
    
    qualityHistory = {
        'face': deque(maxlen=QUALITY_QUEUE_MAXLEN),
        'eyeLeft': deque(maxlen=QUALITY_QUEUE_MAXLEN),
        'eyeRight': deque(maxlen=QUALITY_QUEUE_MAXLEN)
    }

    # Queues storing most recent position rectangles, used to calculate
    # moving averages
    rectHistory = {
        'face': deque(maxlen=QUEUE_MAXLEN),
        'eyeLeft': deque(maxlen=QUEUE_MAXLEN),
        'eyeRight': deque(maxlen=QUEUE_MAXLEN)
    }

    # Moving average of position rectangles
    rectAverage = {
        'face': numpy.array([]),
        'eyeLeft': numpy.array([]),
        'eyeRight': numpy.array([])
    }

    def add(self, rects):
        """Add new set of rectangles to model"""

        # Checks to see if face has moved significantly. If so, resets history.
        if (self._faceHasMoved(rects['face'])):
            self.clear()

        # Loop over rectangles, adding non-empty ones to history
        for key, rect in rects.items():
            if len(rect) is not 4:
                self.qualityHistory[key].append(0)
                continue
            self.rectHistory[key].append(rect)
            self.qualityHistory[key].append(1)
        #			print 'appended to qHist[',key,']'

        # Update moving average stats
        self._updateAverages()

    def getPreviousFaceRects(self):
        if len(self.rectHistory['face']) is 0:
            return numpy.array([], dtype=numpy.int64)
        else:
            return self.rectHistory['face'][-1]

    def getEyeRects(self):
        """Get array of eye rectangles"""
        return [self.rectAverage['eyeLeft'], self.rectAverage['eyeRight']]

    def getFaceRect(self):
        """Get face rectangle"""
        return self.rectAverage['face']

    def getEyeLine(self):
        """Returns Points to create line along axis of eyes"""
        left, right = self.getEyeRects()

        if len(left) is not 4 or len(right) is not 4:
            return [(0, 0), (0, 0)]

        leftPoint = (left[0], ((left[1] + left[3]) / 2))
        rightPoint = (right[2], ((right[1] + right[3]) / 2))
        return [leftPoint, rightPoint]

    def clear(self):
        """ Resets Eye History"""
        for key, value in self.rectAverage.items():
            self.rectAverage[key] = numpy.array([], dtype=numpy.int64)
            self.rectHistory[key].clear()
            self.qualityHistory[key].clear()

    def _faceHasMoved(self, recentFaceRect):
        """Determines if face has just moved, requiring history reset"""

        # If no face found, return true
        if (len(recentFaceRect) is not 4):
            return True

        history = self.rectHistory['face']

        if len(history) is not self.QUEUE_MAXLEN:
            return False

        old = history[self.QUEUE_MAXLEN - 10]
        oldX = (old[0] + old[2]) / 2.0
        oldY = (old[1] + old[3]) / 2.0
        recentX = (recentFaceRect[0] + recentFaceRect[2]) / 2.0
        recentY = (recentFaceRect[1] + recentFaceRect[3]) / 2.0
        change = ((recentX - oldX) ** 2 + (recentY - oldY) ** 2) ** 0.5  # sqrt(a^2+b^2)
        return True if change > 15 else False

    def _updateAverages(self):
        """Update position rectangle moving averages"""
        for key, queue in self.rectHistory.items():
            if len(queue) is 0:
                continue
            self.rectAverage[key] = sum(queue) / len(queue)

        faceQ = numpy.mean(self.qualityHistory['face'])
        eyeLeftQ = numpy.mean(self.qualityHistory['eyeLeft'])
        eyeRightQ = numpy.mean(self.qualityHistory['eyeRight'])
        print('Face Quality: ',faceQ, ' LeftEye Quality: ', eyeLeftQ, ' RightEye Quality: ', eyeRightQ)
    	# print 'QHistory: ', self.qualityHistory['face'], self.qualityHistory['eyeLeft'], self.qualityHistory['eyeRight']
    	# print '--------------'

    # print 'QHistSizes: ', len(self.qualityHistory['face']), len(self.qualityHistory['eyeLeft']), len(self.qualityHistory['eyeRight'])

