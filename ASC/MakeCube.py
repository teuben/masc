#! /usr/bin/env python
#
#	load a cube with the given command line arguments


import ASCube
import Dtime
import logging
import argparse as ap
import copy
from astropy.io import fits

if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO)
    dt = Dtime.Dtime("mplot1") 
    
    #--box x1 y1 x2 y2
    parser = ap.ArgumentParser(description='Plotting .fits files.')

    # todo: it allows us to index above and below the given boundaries
    parser.add_argument('-b', '--box', nargs = 4, type = int, default = [1, 1, 1342, 1040], help = 
    	'Coordinates for the bottom left corner and ' 
       + 'top right corner of a rectangle of pixels to be analyzed from the' + 
       ' data. In the structure x1, y1, x2, y2 (1 based numbers).' +
       ' Box coordinates should be strictly positive or 0, with x1 <= x2 and y1 <= y2')

    parser.add_argument('-d', '--dirname', nargs = 1, type = str, default = ['.'],
        help = 'Name of the directory containing data')

    parser.add_argument('-f', '--frames', nargs = 1, type = str, default = ['0'],
        help = 'The frames wanted, written in the form <start>:<end>:<step>,'+
        '<start>:<end>:<step>,... Be sure to not put in any spaces.')

    parser.add_argument('-m', '--maxframes', nargs = 1, type = int, default = 10000,
        help = 'The highest possible frame value')

    parser.add_argument('-t', '--template', nargs = 1, type = str, default = ["IMG%05d.FIT"],
        help = 'The template of file names for images taken.')

    parser.add_argument('-o', '--outcube', nargs = 1, type = str, default = ["cube.fits"],
    	help = 'The name you want for the cube file that is generated, defaulted to ' +
    	'cube.FITS')

    parser.add_argument('-v', '--verbose', action = "store_true", default = False,
    	help = 'Flag to activate verbose mode.')

    parser.add_argument('-n', '--noload', action="store_true", default = False, 
        help = 'Flag to avoid loading the entire file')

    parser.add_argument('-D', '--difference', action="store_true", default = False, 
        help = 'Flag to determine if you want the difference cube')

    parser.add_argument('-S', '--sig_frames', action="store_true", default = False, 
        help = 'Flag to determine if you want the significant frames only')

    parser.add_argument('-M', '--meteors', action="store_true", default = False, 
        help = 'Flag to find interesting time-variable objects.')

    args = vars(parser.parse_args())

    dt.tag("after parser")

    dirname = args['dirname'][0]
    frames = ASCube.strToIntArray(args['frames'][0])
    box = args['box']
    maxframes = args['maxframes']
    template = args['template'][0]
    doload = not args['noload']
    outcube = args['outcube'][0]
    difference = args['difference']
    sig = args['sig_frames']
    met = args['meteors']

    dt.tag("before ASCube")
    cube = ASCube.ASCube(dirname, box, frames, maxframes, template, doload, difference, sig, met)

    header = copy.copy(cube.headers[0])
    header['NAXIS'] = 3
    header['NAXIS3'] = cube.numfiles
    fits.writeto( outcube, cube.data, header, clobber=True )

    dt.end()


