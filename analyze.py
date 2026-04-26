from ast import Constant
from typing import Any, BinaryIO
import io, srsly

arr_col1: list[type[int]] = []
arr_col2: list[type[int]] = []
arr_col3: list[type[int]] = []
arr     : list[type[int]] = []

read_file: io.TextIOWrapper # pyright: ignore[reportPrivateUsage]
write_report: io.TextIOWrapper # pyright: ignore[reportPrivateUsage]
write_data: BinaryIO
     #tuple[ 0   1   2        3           4         5    ]
     #tuple[max,min,mean,total_count,zero_count,num_count]
#col1: tuple[int,int,int,int,int,int]
col1: dict[str,int] = {}
col2: dict[str,int] = {}
col3: dict[str,int] = {}
#col1 =  {"max"  : 0,
         #"min"  : 0,
         #"mean" : 0,
         #"total": 0,
         #"zero" : 0,
         #"nums" : 0}
col1List = [0] * 6
#col2 =  {"max"  : 0,
         #"min"  : 0,
         #"mean" : 0,
         #"total": 0,
         #"zero" : 0,
         #"nums" : 0}
col2List = [0] * 6
#col3 =  {"max"  : 0,
         #"min"  : 0,
         #"mean" : 0,
         #"total": 0,
         #"zero" : 0,
         #"nums" : 0}
col3List = [0] * 6
#col2: tuple[int,int,int,int,int,int]
#col3: tuple[int,int,int,int,int,int]
exclusive: bool = True

#def set_file()->io.TextIOWrapper[io._WrappedBuffer]:
    #file = open("scan05261995.txt", 'r', True)
    #return file

def set_line(line:str)->tuple[int,int,int]:
    global arr_col1, arr_col2, arr_col3
    lineList: list[str] = line.split()
    lineTuple: tuple = (int(lineList[0]),int(lineList[1]),int(lineList[2]))
    arr_col1.append(lineTuple[0])
    arr_col2.append(lineTuple[1])
    arr_col3.append(lineTuple[2])
    arr.append(lineTuple[0])
    arr.append(lineTuple[1])
    arr.append(lineTuple[2])
    return lineTuple

def setColTuples(line:tuple[int,int,int])->None:
    global col1List, col2List, col3List
    i:int = 0
    for list in col1List,col2List,col3List:
        if list[0] <= line[i]:
            list[0] = line[i]
        if list[1] >= line[i]:
            list[1] = line[i]
        list[2] += line[i]
        list[3] += 1
        if line[i] == 0:
            list[4] += 1
        else:
            list[5] += 1

def setDict()->None:
    global col1,col2,col3,col1List,col2List,col3List
    for dictionary,list in zip((col1,col2,col3), (col1List,col2List,col3List)):
        max = list[0]
        min = list[1]
        total = list[3]
        mean = list[2] // total
        zero = list[4]
        nums = list[5]
        
        dictionary.update({"max"  : max})
        dictionary.update({"min"  : min})
        dictionary.update({"mean" : mean})
        dictionary.update({"total": total})
        dictionary.update({"zero" : zero})
        dictionary.update({"nums" : nums})
            
def writeReport()->None:
    global col1List,col2List,col3List,write_report
    lines = f"""
|========|==========|==========|==========|
|  Data  | Column 1 | Column 2 | Column 3 |
|========|==========|==========|==========|
|--Max---|-{col1List[0]:<8}-|-{col2List[0]:<8}-|-{col3List[0]:<8}-|
|--Min---|-{col1List[1]:<8}-|-{col2List[1]:<8}-|-{col3List[1]:<8}-|
|--Mean--|-{(col1List[2] // col1List[3]):<8}-|-{(col2List[2] // col2List[3]):<8}-|-{(col3List[2] // col3List[3]):<8}-|
|--Total-|-{col1List[3]:<8}-|-{col2List[3]:<8}-|-{col3List[3]:<8}-|
|--0Count|-{col1List[4]:<8}-|-{col2List[4]:<8}-|-{col3List[4]:<8}-|
|--#Count|-{col1List[5]:<8}-|-{col2List[5]:<8}-|-{col3List[5]:<8}-|
|========|==========|==========|==========|
"""
    print(lines)
    _ = write_report.write(lines)


def writeData()->None: 
    global arr_col1,arr_col2, arr_col3, arr
    global col1,col2,col3,write_data, write_report
    demarc   = bytes("00000000", "utf-8")
    col1Data = srsly.pickle_dumps(col1)
    arr1Data = srsly.pickle_dumps(arr_col1)
    col2Data = srsly.pickle_dumps(col2)
    arr2Data = srsly.pickle_dumps(arr_col2)
    col3Data = srsly.pickle_dumps(col3)
    arr3Data = srsly.pickle_dumps(arr_col3)
    arrayData= srsly.pickle_dumps(arr)
    oneD     = write_data.write(col1Data)
    one      = write_data.write(arr1Data)
    demarc1  = write_data.write(demarc)
    twoD     = write_data.write(col2Data)
    two      = write_data.write(arr2Data)
    demarc2  = write_data.write(demarc)
    threeD   = write_data.write(col3Data)
    three    = write_data.write(arr3Data)
    demarc3  = write_data.write(demarc)
    array    = write_data.write(arrayData)
    total = oneD + one + demarc1 + twoD + two + demarc2 + threeD + three + demarc3 + array
    string   = f"""Wrote Bytes: 
\tColumn 1:
\t\tColumn 1 Dictionary: {oneD:<13} Bytes
\t\tColumn 1 Array     : {one:<13} Bytes
\tColumn 2:
\t\tColumn 2 Dictionary: {twoD:<13} Bytes
\t\tColumn 2 Array     : {two:<13} Bytes
\tColumn 3:
\t\tColumn 3 Dictionary: {threeD:<13} Bytes
\t\tColumn 3 Array     : {three:<13} Bytes
\tTotal:
\t\tArray Size         : {array:<13} Bytes
\t\tTotal Size         : {total:<13} Bytes
"""
    print(string)
    _ = write_report.write(string)
    


def main()->None:
    global read_file, write_report, write_data
    file_name: str = "output"
    data_name = file_name
    data_name += ".dump"
    file_name += ".txt"

    try:
        read_file = open("scan05261995.txt", 'r', True) 
        write_report = open(file_name, "w", True)
        write_data = open(data_name, "w+b", True)

        i: int = 0
        tup: tuple
        for line in read_file:
            tup = set_line(line)
            setColTuples(tup)
            i += 1
            if i % 10000 == 0:
                line = f"Line {i}: {tup}"
                print(line)
                _ = write_report.write(line)
        line = f"Total Number of lines = {i}"
        print(line)
        _ = write_report.write(line)
        setDict()
        writeReport()
        writeData()

    except Exception.with_traceback as e:
        print("FAILURE")
        print(e)
        
    finally:
        read_file.close()
        write_report.close()
        write_data.close()

        
if __name__ == "__main__":
    main()


    
    
    

