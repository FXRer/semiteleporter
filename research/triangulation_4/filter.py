from sys import argv
import cv2
import numpy as np

RedMask = np.array([[[0, 0, 1]]])


def calibrationMask(img_with, img_without):
    res = substract(img_with, img_without)
    res = filterNoise(res)
    return (res-1)/255
    

def substract(image_with_lasers, image_without_lasers):
    """
    Substract the image without lasers from the one with lasers.
    @param image_with_lasers A (heigh, width, 3) shaped NumPy array
    @param image_without_lasers A (heigh, width, 3) shaped NumPy array
    """
    assert image_with_lasers.shape == image_without_lasers.shape
    assert len(image_with_lasers.shape) == 3
    assert image_with_lasers.shape[2] == 3
    global RedMask

    if(RedMask.shape != image_with_lasers.shape):
        RedMask = np.array(image_with_lasers.shape, dtype=np.int16)
        RedMask[:] = [0, 0, 1]
        #RedMask = np.zeros(image_with_lasers.shape, dtype=np.int16)
        #RedMask[270:800,730:1120] = [0, 0, 1]
    res = np.array(image_with_lasers*RedMask - image_without_lasers*RedMask, dtype=np.int16)
    return np.array(res.clip(0), dtype=np.uint8)

def filterNoise(img):
    """Apply filters to remove lonesome points"""
    img = cv2.GaussianBlur(img,(5,5),0)
    ret, img = cv2.threshold(img, 27, 255, cv2.THRESH_TOZERO)
    return img

def massCenter(img, limit=None, output=None):
    """
    Search mass center of the red color by line in each area delimited by limit
    """
    height,x,y = 0,0,0
    parts = []
    res = [[],[]]

    if(limit == None):
        height = img.shape[0]
    else:
        height = len(limit)

    for line in range(height):
        if(limit == None):
            x,y = img.shape[1], line
            parts = [img[y,:,2]]
        else:
            x,y = limit[line]
            parts = [img[y,:x,2], img[y,x:,2]]
            
        for side in range(len(parts)):
            moments = cv2.moments(parts[side])
            if(moments['m00'] != 0):
                point = [round(moments['m01']/moments['m00']+x*side), y]
                res[side].append(point)
                if (output != None):
                    output[point[1]][point[0]] = np.array([0,255,0], dtype=np.uint8)

    return res[0]+res[1]

def linearRegression(points, output=None):
    """
    Apply linear regression on all points
    """
    x,y = np.array(points).T
    param = np.linalg.lstsq(np.array([y, np.ones(y.shape)]).T, x)[0]
    line = np.array([param[0]*y+param[1],y]).T

    if output != None:
        for x,y in line:
            output[y][x] = np.array([255,0,0], dtype=np.uint8)
    
    return line

def display(img, title):
    """Show results (demo)"""
    cv2.imshow(title, cv2.resize(img, (640, 360), interpolation=cv2.INTER_AREA))
    cv2.waitKey(0)

def findPoints(_with, without):
    img = filterNoise(substract(_with, without))
    points = massCenter(img, None, img)
    points = linearRegression(points, img)
    return massCenter(img, points, img)

if(__name__ == "__main__"):
    import matplotlib.pyplot as plt
    wi, wo = cv2.imread(argv[1]), cv2.imread(argv[2])

    display(wi, "Avec lasers")
    display(wo, "Sans lasers")

    img = substract(wi, wo)
    display(img, "Substraction result")

    img = filterNoise(img)
    display(img, "soft filter to delete noise")

    points = massCenter(img, None, img)
    display(img,"First mass center step")

    #points = linearRegression(points, img)
    #display(img, "linear regression result")

    #wi *= 0.25
    #points = massCenter(img, points, wi)
    #display(wi,"Second mass center step to fit lasers")

    X, Y = map(np.array,  zip(*points))
    plt.scatter(X, -Y)
    plt.xlim(0, 1920)
    plt.ylim(-1080, 0)
    plt.show() 
