from ctypes import ArgumentError
from numpy.typing import NDArray
from PIL import Image, ImageEnhance
import io, numpy, sys 
sys.setrecursionlimit(2000) #Used for upscaling functions


dictList   : list[type[dict]] = []
arrList    : list[type[list[type[int]]]] = []
returnHold : list[list[tuple[int,int,int]]]

givenName       = "scan05261995.txt"
scanUpscale     = "scanUpscale.txt"
scanInterpolate = "scanInterpolate.txt"


def test_numpy()->None:
    """test_numpy Tester to load the data of the image into a numpy array, contained here for sake of archival
    """
    global givenName
    data= numpy.loadtxt(givenName, delimiter=' ', dtype=numpy.int16)
    file:io.TextIOWrapper
    file= open("test.out", "w", True)
    for i in range(300):
        if i < 30:
            print(f'First 30 Numbers:')
            print(f'\tNumber {i}: {data[i*10000]} \n')
            print(f'Wrote: {file.write((f"Line {i * 10000}:") + str(data[i * 10000]) + "\n")}')
        
    file.close()

def load_array(filename: str | None)->NDArray:
    """load_array Loads scan array from file name given (Doesn't actually transfer file name since it didn't seem to want to work)


    :param str | None filename: Idea here was to allow for dynamic loading into numpy array, didn't end up working
    :return NDArray: Numpy array of image
    """
    global givenName, dictList, arrList
    data: NDArray
    
    filename = givenName
    #if filename is None:
    #filename = givenName
    data    = numpy.loadtxt(filename, delimiter=' ', dtype=numpy.uint8)
    reshape = numpy.reshape(data, (480,640,3))
    return reshape

def ndarray_to_tuple_list(ndarray: NDArray)->list[tuple[int,int,int]]:
    """ndarray_to_tuple_list Converts a given numpy array into a singular long list of pixel tuples


    :param NDArray ndarray: numpy array (Can be of any size)
    :return list[tuple[int,int,int]]: Array of pixel values represented by a tuple of r,g,b
    """
    arr: list[tuple[int,int,int]] = []
    tempList: list[int] = []
    for vertical in ndarray:
        for horizontal in vertical:
            tempList.clear()
            for item in horizontal:
                tempList.append(item)
            tup = (int(tempList[0]),int(tempList[1]),int(tempList[2]))
            arr.append(tup)

    return arr

def ndarray_to_list_list(ndarray: NDArray)->list[list[list[int]]]:
    """ndarray_to_list_list Compatibility layer to transfer numpy array to 2d array of *list* pixels


    :param NDArray ndarray: Array of unspecified size
    :return list[list[list[int]]]: 2D array of pixels, represented by a list of pixels (Only first three values, expects r,g,b)
    """
    arr: list[list[list[int]]] = []
    for rowCount,row in enumerate(ndarray):
        arr.append([])
        for col in row:
            arr[rowCount].append(col)
    return arr

def test_vga_file(ndarray: NDArray)->None:
    """test_vga_file Another tester function, analyzes size of loaded numpy array

    _extended_summary_

    :param NDArray ndarray: numpy array to analyze and write size to file (test_ndarray.txt)
    """
    i : int = 0
    j : int = 0
    with open("test_ndarray.txt", 'w', True) as file : 
        for vertical in ndarray:
            i+= 1
            _ = file.write(f"Array {i}: ")
            for horizontal in vertical:
                j+=1
                _ = file.write("[ ")
                for item in horizontal:
                    _ = file.write(f'{item} ')
                _ = file.write("]-")
            _ = file.write(f"size: {j}\n")
            j = 0

def r_or_g_or_b(pixel:tuple[int,int,int] | list[int])->int | None:
    """r_or_g_or_b Takes a pixel value and returns a int based on the position of first non-zero value, or None if all zero


    :param tuple[int,int,int] | list[int] pixel: Pixel of arbitrary array type consisting of 3 r,g,b int values
    :return int | None: Returns int of position (0=r,1=g,2=b) or None if all zero
    """
    i: int = 0
    for color in pixel:
        if color != 0:
            return i
        i += 1
    return None

def upscale_determine_intermediate(left: tuple[int,int,int] | None, right:tuple[int,int,int] | None, above: tuple[int,int,int] | None, below: tuple[int,int,int] | None)->tuple[int,int,int]:
    """upscale_determine_intermediate Takes pixel values from adjacent pixels (if they exist) and returns averaged value

    Note that since this is used for a upscaling function that the 'right' pixel is used as the expansionary pixel and so is almost always None (expand row recursively from left->right)

    :param tuple[int,int,int] | None left: Current pixel / Expansionary pixel
    :param tuple[int,int,int] | None right: Current pixel / Expansionary pixel
    :param tuple[int,int,int] | None above: Pixel directly above
    :param tuple[int,int,int] | None below: Pixel directly below
    :return tuple[int,int,int]: Average of above values
    """
    denominator: int = 4
    if left is None:
        left = (0,0,0)
        denominator -= 1
    if right is None:
        right = (0,0,0)
        denominator -= 1
    if above is None:
        above = (0,0,0)
        denominator -= 1
    if below is None:
        below = (0,0,0)
        denominator -= 1

    nums: list[int] = []
    for i in range(3):
        mean = (left[i] + right[i] + above[i] + below[i]) // denominator
        nums.append(mean)
    return (nums[0], nums[1], nums[2])
    
# BEFORE
#             a   b   c
#             d   e   f
#             g   h   i
# AFTER ROW
#             a   1   b   2   c   3
#             d   4   e   5   f   6
#             g   7   h   8   i   9
# AFTER COL
#             a   1   b   2   c   3
#             A   B   C   D   E   F
#             d   4   e   5   f   6
#             G   H   I   J   K   L
#             g   7   h   8   i   9
#             M   N   O   P   Q   R


def upscale_col(raw: list[tuple[int,int,int]])->list[list[tuple[int,int,int]]]:
    """upscale_col Simultaneously expands given singular list of pixel tuples into 2d array of pixel tuples, and also expands each column right by one

    :param list[tuple[int,int,int]] raw: List of pixels
    :return list[list[tuple[int,int,int]]]: Returns newly expanded 2d array of stretched pixel values
    """
    global returnHold
    row_num: int = 0
    col_num: int = 0
    width: int = 640
    height: int = 480
    left: int = 0
    right: int = 1
    above: int = 2
    below: int = 3
    i: int = 0
    after_col: list[list[tuple[int,int,int]]] = [[]]
    is_not_right: bool = False
    
    for num,pixel in enumerate(raw):
        after_col[i].append(pixel)
        surrounding: list[tuple[int,int,int] | None] = [(0,0,0),None,None, None]
        col_num += 1
        surrounding[left] = pixel #left
        #Calculate if rightmost
        is_not_right = bool(col_num % width)
        if is_not_right: #right
            surrounding[right] = raw[num + 1]
        #Calculate if top or bottom
        if num % height == 0:
            row_num += 1
        #Calculate Above
        if row_num > 1: #above
            surrounding[above] = raw[num - width]
        #Calculate Below
        if row_num < height: #below
            surrounding[below] = raw[num + width]
        avg = upscale_determine_intermediate(surrounding[0], surrounding[1],surrounding[2],surrounding[3])
        after_col[i].append(avg)
        #between.append(avg)
        if is_not_right is False:
            i += 1
            after_col.append([])
            #after_col.append(between)
            #between.clear()
            col_num = 0

    _ = after_col.pop()

    return after_col

def upscale_aprox_row(rowAbove: list[tuple[int,int,int]] | None, rowBelow:list[tuple[int,int,int]] | None)->list[tuple[int,int,int]]:
    """upscale_aprox_row Takes row from above and row from below to approximate another row, with mixed results

    _extended_summary_

    :param list[tuple[int,int,int]] | None rowAbove: Row above (Current row), Optional None since there is chance of miscall
    :param list[tuple[int,int,int]] | None rowBelow: Row below (Row to expand to)
    :raises ArgumentError: Will raise argError if row above is None
    :return list[tuple[int,int,int]]: returns new row
    """
    if rowAbove is None:
        raise ArgumentError("rowAbove passed to upscale aprox row is Null...").with_traceback(None)
    #print(len(rowAbove))
    if len(rowAbove) == 1:
        if rowBelow is None:
            return [upscale_determine_intermediate(None,None,rowAbove[-1],None)]
        else:
            return [upscale_determine_intermediate(None,None,rowAbove[-1],rowBelow[-1])]
    call: list[tuple[int,int,int]]
    if rowBelow is None:
        call = upscale_aprox_row(rowAbove[:-1],None)
        call.append(upscale_determine_intermediate(None,call[-1],rowAbove[-1], None))
    else:
        call = upscale_aprox_row(rowAbove[:-1],rowBelow[:-1])
        call.append(upscale_determine_intermediate(None,call[-1],rowAbove[-1], rowBelow[-1]))
    return call

def upscale_row(dim: list[list[tuple[int,int,int]]])->list[list[tuple[int,int,int]]]:
    """upscale_row Takes 2d array of rows and columns and expands every row by one, effectively stretching the image vertically by 2x

    _extended_summary_

    :param list[list[tuple[int,int,int]]] dim: 2d array of pixel values
    :return list[list[tuple[int,int,int]]]: 2d array of (stretched!) pixel values
    """
    between: list[list[tuple[int,int,int]]] = []
    for rn,row in enumerate(dim):
        row_below = rn + 1
        between.append(row)
        if (row_below >= len(dim)):
            between.append(upscale_aprox_row(row,None))
        else:
            below = dim[row_below]
            between.append(upscale_aprox_row(row, below))
            
        #print(f'row {above} has length: {len(dim[above])} first && last value : {dim[above][0]}, {dim[above][-1]}')
    #print(len(between))
    return between

def upscale(raw: list[tuple[int,int,int]])->Image.Image:
    """upscale Takes simple array of pixel values and returns a 2x upscaled image of the original array


    :param list[tuple[int,int,int]] raw: Long list of pixel values expressed as tuple
    :return Image.Image: Newly upscaled image
    """
    global returnHold, scanUpscale
    stretchedHorizontal: list[list[tuple[int,int,int]]] = upscale_col(raw)
    #print(f"\tRow ")
    upscaled: list[list[tuple[int,int,int]]] = upscale_row(stretchedHorizontal)
    upscaledLists: list[list[list[int]]] = changeTuple(upscaled)
    ndarray: NDArray = write_data(upscaledLists, scanUpscale).astype(numpy.uint8)

    upscaleImage = Image.fromarray(ndarray,"RGB")
    return upscaleImage

def write_data(raw: list[list[list[int]]], fileToWrite : str)->NDArray:
    """write_data Writes given pixel values (as a scan list) to specified file and returns the scanned numpy array from temp file (does not delete temp file)

    :param list[list[list[int]]]: pixel values to scan into numpy array
    :param str fileToWrite: file to use as temp file
    :return NDArray: Scanned numpy array loaded from temp file
    """
    global scanUpscale, scanInterpolate
    with open(fileToWrite,"w",True) as file:
        for row in raw:
            for col in row:
                _ = file.write(f'{col[0]} {col[1]} {col[2]}\n')
    data = numpy.loadtxt(fileToWrite, delimiter=' ', dtype=numpy.uint8)
    reshape: NDArray
    if fileToWrite == scanUpscale:
        reshape = numpy.reshape(data,(960,1280,3))
    else:
        reshape = numpy.reshape(data,(480,640,3))
    return reshape

def changeTuple(original: list[list[tuple[int,int,int]]])->list[list[list[int]]]:
    """changeTuple Compatibility to change 2d array of *tuple* pixel values to *list* pixel values


    :param list[list[tuple[int,int,int]]] original: Tuple 2d array
    :return list[list[list[int]]]: List 2d array
    """
    ret: list[list[list[int]]] = []
    for rn, row in enumerate(original):
        ret.insert(rn, [])
        for cn, col in enumerate(row) : 
            ret[rn].insert(cn, [col[0], col[1], col[2]])

    for row in ret:
        for col in row:
            if len(col) != 3:
                print("NON 3 PIXEL")
            if isinstance(col,tuple):
                print("is tuple")
    return ret

def enhance(original: Image.Image, base: str)->list[Image.Image] : 
    """enhance uses base Image.enhance functions to try to 'enhance' image from given Image and writes base file name + enhance type


    :param Image.Image original: Image to enhance
    :param str base: Base filename
    :return list[Image.Image]: List of all enhanced images
    """
    c          = ImageEnhance.Color(original)
    ct         = ImageEnhance.Contrast(original)
    s          = ImageEnhance.Sharpness(original)
    b          = ImageEnhance.Brightness(original)
    color      = c.enhance(5.0)
    contrast   = ct.enhance(5.0)
    sharpness  = s.enhance(5.0)
    brightness = b.enhance(5.0)
    color.save(base + "_color.jpg")
    contrast.save(base + "_contrast.jpg")
    sharpness.save(base + "_sharpness.jpg")
    brightness.save(base + "_brightness.jpg")
    return [color,contrast,sharpness,brightness]

def safe_int_divide(dividend: int, divisor: int)->int:
    """safe_int_divide Safely divides two ints by reducing incidence of zero divide for recursion safety reasons

    :raises ZeroDivisionError: Will raise error if zero divide is attempted
    :return int: Returns divided value
    """
    if divisor == 0:
        if dividend == 0:
            return 0
        raise ZeroDivisionError(f"CANNOT DIVIDE {dividend} by zero")
    return dividend // divisor
#                         [[ROW[PIXEL]ROW], [ROW[PIXEL]ROW], [ROW[PIXEL]ROW]]
def interpolate(original: NDArray)->NDArray:
    """interpolate Interpolates given 2d numpy array of pixel values

    :param NDArray original: numpy array to average
    :return NDArray: Interpolated numpy array
    """
    global scanInterpolate
    listImage: list[list[list[int]]] = []
    vertSize : int = len(original) - 1
    currentHoriIndex : int = 0
    original = original.astype(numpy.uint16)
    #currentVertIndex : int = 0

    for currentHoriIndex,horizontal in enumerate(original) : 
        horiSize : int = len(horizontal) - 1
        listImage.insert(currentHoriIndex, [])
        for currentPixelIndex,pixel in enumerate(horizontal) : 
            try:
                myPixel: list[int] = pixel
                theirPixel: list[int]
                count: list[int] = [0,0,0] # Number of Rs, Number of Gs, Number of Bs
                values: list[int]= [0,0,0]
                myType: int | None = r_or_g_or_b(pixel)
                theirType: int | None = None

                if currentPixelIndex - 1 > 0: #left column
                    theirPixel = original[currentHoriIndex][currentPixelIndex - 1] #left of me
                    theirType = r_or_g_or_b(theirPixel)
                    if theirType is not None:
                        count[theirType] += 1
                        values[theirType] += theirPixel[theirType]

                    if currentHoriIndex > 0:         #top left column
                        theirPixel = original[currentHoriIndex - 1][currentPixelIndex - 1]
                        theirType = r_or_g_or_b(theirPixel)
                        if theirType is not None:
                            count[theirType] += 1
                            values[theirType] += theirPixel[theirType]

                    if currentHoriIndex < vertSize : #bottom left column
                        theirPixel = original[currentHoriIndex + 1][currentPixelIndex - 1]
                        theirType = r_or_g_or_b(theirPixel)
                        if theirType is not None:
                            count[theirType] += 1
                            values[theirType] += theirPixel[theirType]
                if myType is not None:        #My column
                    count[myType] += 1
                    values[myType] = myPixel[myType]
                if currentHoriIndex > 0:      # Direct Above
                    theirPixel = list(original[currentHoriIndex - 1][currentPixelIndex])
                    theirType  = r_or_g_or_b(theirPixel)
                    if theirType is not None:
                        count[theirType] += 1
                        values[theirType] += theirPixel[theirType]
                if currentHoriIndex < vertSize: # Direct Below
                    theirPixel = list(original[currentHoriIndex + 1][currentPixelIndex])
                    theirType  = r_or_g_or_b(theirPixel)
                    if theirType is not None:
                        count[theirType] += 1
                        values[theirType] += int(theirPixel[theirType])
                if currentPixelIndex < horiSize : #right column
                    if currentHoriIndex > 0: # top right
                        theirPixel = list(original[currentHoriIndex - 1][currentPixelIndex + 1])
                        theirType  = r_or_g_or_b(theirPixel)
                        if theirType is not None:
                            count[theirType] += 1
                            values[theirType] += theirPixel[theirType]
                    theirPixel = original[currentHoriIndex][currentPixelIndex + 1] # Direct right
                    theirPixel = recast_int(theirPixel)
                    theirType  = r_or_g_or_b(theirPixel)
                    if theirType is not None:
                        count[theirType] += 1
                        #print(f'values: {values[theirType]}, pixel: {theirPixel[theirType]}')
                        values[theirType] += int(theirPixel[theirType])
                    if currentHoriIndex < vertSize:
                        theirPixel = list(original[currentHoriIndex + 1][currentPixelIndex + 1]) # Below right
                        theirType  = r_or_g_or_b(theirPixel)
                        if theirType is not None:
                            count[theirType] += 1
                            values[theirType] += theirPixel[theirType]

                after = [safe_int_divide(values[0],count[0]) , safe_int_divide(values[1], count[1]) , safe_int_divide(values[2], count[2])]
                listImage[currentHoriIndex].insert(currentPixelIndex, after)
            except Exception as e:
                print("UH OH!")
                print(e)
                for i in range(3):
                    print(f'VALUES: {values[i]}')  # pyright: ignore[reportPossiblyUnboundVariable]
                    print(f'PIXEL : {theirPixel[i]}')  # pyright: ignore[reportPossiblyUnboundVariable]
    array: NDArray = write_data(listImage, scanInterpolate)
    return array
    #fromarray: Image.Image = Image.fromarray(array, "RGB")
    #return fromarray

def recast_int(arr)->list[int]:
    """recast_int Deprecated function to take array of numpy data type and cast to list of ints is effectively useless

    :param _type_ arr: Array of [numerical] data types
    :return list[int]: Array as list of ints
    """
    retList: list[int] = []
    for numbers in arr:
        retList.append(int(numbers))
        
    return retList

def main():
    #test_numpy()
    ndarray = load_array(None)
    #print(ndarray)
    
    tupleArray = ndarray_to_tuple_list(ndarray)
    #print(f"Number of rows: {len(tupleArray)}")
    #for i in range(10):
        #print(f'\tRow {i + 1} length: {len(tupleArray[i])}')
    #arrowArray = arrow.array(tupleArray)
    #fromArrow = Image.fromarrow(arrowArray, "RGB", (640,480))
    #print(f"from array function image size: {fromArray.size}")
    #print(f'Width = {fromArray.width}\nLength = {fromArray.height}')
    #print(f'Get pixel 1, 2 {fromArray.getpixel((0,0))}, {fromArray.getpixel((1,0))}')

    interpolated = interpolate(ndarray)
    interpolateTuple = ndarray_to_tuple_list(interpolated)
    upscaledInterpolate = upscale(interpolateTuple)

    fromArray = Image.fromarray(ndarray,"RGB")
    upscaledImage = upscale(tupleArray)
    interpolatedImage = Image.fromarray(interpolated, "RGB")

    fromArray.save("base.jpg")
    upscaledImage.save("upscaled.jpg")
    interpolatedImage.save("interpolate.jpg")


    _        = enhance(fromArray,     "base")
    _        = enhance(upscaledImage, "upscaled")
    _        = enhance(interpolatedImage, "interpolate")
    _        = enhance(upscaledInterpolate, "upscaledInterpolate")

if __name__ == "__main__":
    main()