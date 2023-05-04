#!/usr/bin/env python-real

import sys
import os
import SimpleITK as sitk
from nrrd import read
import numpy as np
from datetime import date
from tools.crop import crop
from tools.thickness import findSpheres
from tools.fill import fill
from tools.writeReport import writeReport
from tools.largestCC import largestCC
import tools.reader as reader
from DensityAnalysis import densityMap

# Performs analysis on cortical bone
# image: 3D image black and white of bone
# mask: 3D labelmap of bone area, including cavities
# lower, upper: The thresholds for bone in the image. Any pixels with a vaule in the range will be considered bone.
# voxSize: The physical side length of the voxels, in mm 
# slope, intercept and scale: parameters for density conversion
# output: The name of the output directory
def main(inputImg, inputMask, lower, upper, voxSize, slope, intercept, output):   
    imgData=reader.readImg(inputImg)
    (_, maskData) = reader.readMask(inputMask)
    (maskData, imgData) = crop(maskData, imgData)
    depth = np.shape(maskData)[2] * voxSize
    porousBone = (imgData > lower) & (imgData <= upper)
    boneVolume = np.count_nonzero(porousBone) * voxSize**3
    filledMask = np.zeros_like(maskData)
    for sliceNum in range(maskData.shape[2]):
        filledMask[:,:,sliceNum] = fill(maskData[:,:,sliceNum], 5)
    totalVolume = np.count_nonzero(filledMask) * voxSize**3
    medullarVolume = totalVolume-(np.count_nonzero(maskData) * voxSize**3)
    boneArea = boneVolume/depth
    totalArea = totalVolume/depth
    medullarArea = medullarVolume/depth

    # PMOI
    zDist = np.nonzero(maskData)[2]
    zCenter = sum(zDist)/len(zDist)
    pMOI = sum((zDist-zCenter)**2)*voxSize**4
    # Porosity
    porosity = 1 - np.count_nonzero(porousBone)/np.count_nonzero(maskData)
    # Thickness
    maskData = largestCC(maskData)
    maskData = findSpheres(maskData)
    rads = maskData[np.nonzero(maskData)]
    diams = rads * 2 * voxSize
    thickness = np.mean(diams)
    thicknessStd = np.std(diams)
    # Calculate Density
    density = densityMap(imgData, slope, intercept)
    tmd = np.mean(density)
    
    fPath = os.path.join(output, "cortical.txt")

    header = [
        'Date Analysis Performed',
        'File ID',
        'Mean Cortical Thickness (mm)',
        'Cortical Thickness Standard Deviation (mm)',
        'Tissue Mineral Density(mgHA/cm^3)',
        'Porosity',
        'Total Area (mm^2)',
        'Bone Area (mm^2)',
        'Medullary Area (mm^2)',
        'Polar Moment of Interia(mm^4)',
        'Voxel Dimension (mm^3)'
    ]
    data = [
        date.today(),
        fPath,
        thickness,
        thicknessStd,
        tmd,
        porosity,
        totalArea,
        boneArea,
        medullarArea,
        pMOI,
        voxSize
    ]

    writeReport(fPath, header, data)



if __name__ == "__main__":
    if len(sys.argv) < 9:
        print(sys.argv)
        print("Usage: CorticalAnalysis <input> <mask> <lowerThreshold> <upperThreshold> <voxelSize> <slope> <intercept> <output>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5]), float(sys.argv[6]), float(sys.argv[7]), str(sys.argv[8]))

