## Given a .wav audio file, downsamples it to 8000 Hz and writes it out
##  as a ADPCM file suitable for use with AVRs.

from struct import unpack
import wave
import os
import sys


def unpackMono(waveFile):
    w = wave.Wave_read(waveFile)
    data = []
    for i in range(w.getnframes()):
        data.append(unpack("h", w.readframes(1))[0])
    return(data)

def scaleData(data):
    scale = max(max(data), abs(min(data))) * 1.0
    return([x/scale for x in data])

def getDifferences(data):
    differences = []
    for i in range(len(data)-1):
        differences.append(data[i+1]-data[i])
    return(differences)

def quantize(data, thresholds):
    quantized = []
    n = len(thresholds)
    thresholdRange = range(n)
    for d in data:
        categorized = False
        for i in thresholdRange:
            if d <= thresholds[i]:
                quantized.append(i)
                categorized = True
                break
        if not categorized:
            quantized.append(n)
    return(quantized)

def pack4(data):                # for 2-bit data
    packedData = []
    for i in range(len(data) / 4):
        thisByte = 0
        thisByte += 2**6 * data[4*i]
        thisByte += 2**4 * data[4*i+1]
        thisByte += 2**2 * data[4*i+2]
        thisByte += data[4*i+3]
        packedData.append(thisByte)
    return(packedData)

def pack2(data):                # for 1-bit data
    packedData = []
    for i in range(len(data) / 8):
        thisByte = 0
        thisByte += 2**7 * data[8*i]
        thisByte += 2**6 * data[8*i+1]
        thisByte += 2**5 * data[8*i+2]
        thisByte += 2**4 * data[8*i+3]
        thisByte += 2**3 * data[8*i+4]
        thisByte += 2**2 * data[8*i+5]
        thisByte += 2**1 * data[8*i+6]
        thisByte += data[8*i+7]
        packedData.append(thisByte)   
    return(packedData)


def packOneBitDPCM(filename):
    data = unpackMono(filename)
    data = scaleData(data)
    differences = getDifferences(data)
    quantized = quantize(differences, [0])
    packed = pack2(quantized)
    return(packed)

def packTwoBitDPCM(filename):
    data = unpackMono(filename)
    data = scaleData(data)
    differences = getDifferences(data)
    quantized = quantize(differences, TWO_BIT_THRESHOLDS)
    packed = pack4(quantized)
    return(packed)

def createHeader(filename, packedData):
    baseFilename = filename[:-4]
    outfile = open("DPCM_" + baseFilename + ".h", "w")
    outfile.write('const uint8_t DPCM_{}[] PROGMEM = {{\n'.format(baseFilename))
    for byte in packedData:
        outfile.write('  {:d},\n'.format(byte))
    outfile.write('};\n')
    outfile.close()

def testWaveFile(filename):
    w = wave.Wave_read(filename)
    bitrate = w.getframerate()
    channels = w.getnchannels()
    bits = w.getsampwidth()*8
    if not bitrate==8000 or not channels==1 or not bits==16:
        newFilename = filename[:-4] + "_8000.wav"
        returnValue = os.system(SOXCOMMAND.format(filename, newFilename))    
        if returnValue:
            raise(SOX_Exception("Something went wrong calling sox: SOXCOMMAND.format(filename, newFilename"))
        filename = newFilename
    return(filename)
    

class SOX_Exception(Exception):
    pass
class UsageException(Exception):
    pass

if __name__ == "__main__":
    
    TWO_BIT_THRESHOLDS = [-0.05, 0, 0.05]
    try:
        filename = sys.argv[1]
    except IndexError:
        raise(UsageException("usage: python wave2DPCM.py wavefilename.wav"))

    SOXCOMMAND = "sox {} -r 8000 -c 1 -b 16 {}" # for converting wave file
    ## install sox, or use itunes or audacity to convert 
    ## wavefile to 8kHz, 16-bit, one-channel
   
    filename = testWaveFile(filename)
    packedData = packTwoBitDPCM(filename)
    createHeader(filename, packedData)
    
