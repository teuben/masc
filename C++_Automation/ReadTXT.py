#! /usr/bin/env python
#
#    quick and dirty processing of the MD All Sky images

from astropy.io import fits
from scipy.misc import imsave
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import aplpy
import argparse as ap
import os.path
import logging
import time

def d(ff,box=[]):
    #very specific for 16 bit data, since we want to keep the data in uint16
    h = fits.open(ff, do_not_scale_image_data=True)
    if len(box)==0:
        return h[0].header, h[0].data
    else:
        # figure out 0 vs. 1 based offsets; box is 1 based
        return h[0].header, h[0].data[box[1]:box[3], box[0]:box[2]]


def dsum(i0,i1,step = 1, box=[]):
    """ for a range of fits files
        compute the mean and dispersion from the mean
    """
    for i in range(i0,i1+1,step):
        ff = 'IMG%05d.FIT' % i
        h1, d1 = d(ff,box)
        #very specific for 16 bit data, since we want to keep the data in uint16
        bzero = h1['BZERO']
        bscale = h1['BSCALE']
        if i == i0: 
            sum0 = 1.0
            sum1 = d1*bscale+bzero
            sum2 = sum1*sum1
            #sum1 = d1
            #sum2 = d1*d1
            h = h1
            nx = d1.shape[1]
            ny = d1.shape[0]
            nz = i1 + 1 - i0
            c = np.zeros((nz, ny, nx))
            c[0,:,:] = d1.reshape(ny,nx)
        else:
            sum0 = sum0 + 1.0
            sum1 = sum1 + (d1 * bscale + bzero)
            sum2 = sum2 + (d1 * bscale + bzero) * (d1 * bscale + bzero)
            #sum2 = sum2+d1*d1
            c[i - i0,:,:] = d1.reshape(ny,nx)
    sum1 = sum1 / sum0
    sum2 = sum2 / sum0 - sum1*sum1
    print type(sum1), type(sum2)
    return h,sum1,np.sqrt(sum2),c

def show(sum):
    """ some native matplotlib display,
    doesn't show pointsources well at all
    """
    ip = plt.imshow(sum)
    plt.show()

def show2(sum):
    """ aplpy is the better viewer clearly
    """
    fig = aplpy.FITSFigure(sum)
    #fig.show_grayscale()
    fig.show_colorscale()

def show3(sum1,sum2):
    """ aplpy is the better viewer clearly
    """
    fig = aplpy.FITSFigure(sum1,subplot=(2,2,1))
    #fig = aplpy.FITSFigure(sum2,subplot=(2,2,2),figure=1)
    #fig.show_grayscale()
    fig.show_colorscale()

#  For some variations on this theme, e.g.  time.time vs. time.clock, see
#  http://stackoverflow.com/questions/7370801/measure-time-elapsed-in-python
#
class Dtime(object):
    """ Class to help measuring the wall clock time between tagged events
        Typical usage:
        dt = Dtime()
        ...
        dt.tag('a')
        ...
        dt.tag('b')
    """
    def __init__(self, label=".", report=True):
        self.start = self.time()
        self.init = self.start
        self.label = label
        self.report = report
        self.dtimes = []
        dt = self.init - self.init
        if self.report:
            logging.info("Dtime: %s ADMIT " % self.label + str(self.start))
            logging.info("Dtime: %s BEGIN " % self.label + str(dt))

    def reset(self, report=True):
        self.start = self.time()
        self.report = report
        self.dtimes = []

    def tag(self, mytag):
        t0 = self.start
        t1 = self.time()
        dt = t1 - t0
        self.dtimes.append((mytag, dt))
        self.start = t1
        if self.report:
            logging.info("Dtime: %s " % self.label + mytag + "  " + str(dt))
        return dt

    def show(self):
        if self.report:
            for r in self.dtimes:
                logging.info("Dtime: %s " % self.label + str(r[0]) + "  " + str(r[1]))
        return self.dtimes

    def end(self):
        t0 = self.init
        t1 = self.time()
        dt = t1 - t0
        if self.report:
            logging.info("Dtime: %s END " % self.label + str(dt))
        return dt

    def time(self):
        """ pick the actual OS routine that returns some kind of timer
        time.time   :    wall clock time (include I/O and multitasking overhead)
        time.clock  :    cpu clock time
        """
        return np.array([time.clock(), time.time()])

    


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO)
    dt = Dtime("mplot1") 
    
    #--start, -s n
    #--end, -e n
    #--box x1 y1 x2 y2
    parser = ap.ArgumentParser(description='Plotting .fits files.')
    parser.add_argument('-f', '--frame', nargs = '*', type = int, help = 'Starting and ending parameters for the frames analyzed')
    parser.add_argument('-b', '--box', nargs = 4, type = int, help = 'Coordinates for the bottom left corner and top right corner of a rectangle of pixels to be analyzed from the data. In the structure x1, y1, x2, y2 (1 based numbers)')
    parser.add_argument('-g', '--graphics', nargs = 1, type = int, default = 0, help = 'Controls whether to display or save graphics. 0: no graphics, 1: display graphics, 2: save graphics as .png')
    args = vars(parser.parse_args())

    if args['frame'] == None:
        count = 0
        start = None
        end = None
        step = 1
        #while we have yet to find an end
        while end == None:
            filename = 'IMG%05d.FIT' % count
            #if start has not been found yet, and this file exists
            if start == None and os.path.isfile(filename):
                start = count
            #if start has been found and we finally found a file that doesn't exist, set end to the last file that existed (count - 1.FIT)
            elif start != None and not os.path.isfile(filename):
                end = count - 1
            count += 1  
    elif len(args['frame']) >= 2 and len(args['frame']) <= 3:
        start = args['frame'][0]           # starting frame (IMGnnnnn.FIT)
        end   = args['frame'][1]           # ending frame
        if len(args['frame']) == 3:
            step = args['frame']
        else:
            step = 1
    else:
        raise Exception,"-f needs 0, 2, or 3 arguments."
           
    box   = args['box']                # BLC and TRC
    if box == None:
        box = []

    dt.tag("start")
    # compute the average and dispersion of the series        
    h1,sum1,sum2,cube = dsum(start,end,step,box=box)           # end can be uninitialized here might throw an error?
    dt.tag("dsum")
    nz = cube.shape[0]
    
    # delta X and Y images
    dsumy = sum1 - np.roll(sum1, 1, axis = 0)    # change in the y axis
    dsumx = sum1 - np.roll(sum1, 1, axis = 1)    # change in the x axis

    # write them to FITS
    fits.writeto('dsumx.fits', dsumx, h1, clobber=True)
    fits.writeto('dsumy.fits', dsumy, h1, clobber=True)
    fits.writeto('sum1.fits', sum1, h1, clobber=True)
    fits.writeto('sum2.fits', sum2, h1, clobber=True)
    
    
    pixelFile = open('pixels.txt')
    pixelNumber = 0
    pixelData = np.zeros((1392, 1040))
    character  = ' '
    idx = 0
    number = 0
    
    for h in range(0, 1040):
        line = pixelFile.readline()
        for w in range(0, 1392):
            character = line[idx]
            idx = idx + 1
            while character != ',':
                if character != ' ':
                    number = int(character)
                    pixelNumber = (pixelNumber * 10) + number
                character = line[idx]
                idx = idx + 1
            idx = idx + 1
            pixelData[w, h] = pixelNumber 
            pixelNumber = 0
        idx = 0 
    
    fits.writeto('testingPixels.fits', pixelData, h1, clobber=True)      
    
    
    
    dt.tag("write2d")
    # 3D cube to
    h1['NAXIS']  = 3
    h1['NAXIS3'] = nz
    fits.writeto('cube.fits', cube, h1, clobber=True)
    dt.tag("write3d")


    #if args['graphics'][0] == 1:
        # plot the sum1 and sum2 correllation (glueviz should do this)
   #     s1 = sum1.flatten()
   #     s2 = sum2.flatten()
    #    fig = plt.figure()
    #    ax = fig.add_subplot(111)
    #    ax.scatter(s1,s2)
    #    plt.show()
    #    show2(sum1)
    #    show2(sum2)
    #if args['graphics'][0] == 2:
    #    imsave('sum1.png', sum1)
    #    imsave('sum2.png', sum2)
    
    dt.tag("done")
    dt.end()
