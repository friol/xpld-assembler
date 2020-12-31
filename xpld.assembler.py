#
# xpld project - assembler
# friol 2k20
#

import sys;
import array;
import math;
from megaParser import megaParser;
from linker import linker;

glbVersion="0.2";

def title():
    print();
    print("xpld project - assembler v"+glbVersion);


def usage():
    title();
    print("usage: xpld.assembler <filename.xpld> [<binary.bin>]");
    print();

#
# main
#

if len(sys.argv)<2:
    usage();
    sys.exit(1);

inputFileName=sys.argv[1];

title();
print("Processing file ["+sys.argv[1]+"]");

outputFileName="a.bin";
if len(sys.argv)>2:
    print("Output file will be ["+sys.argv[2]+"]");
    outputFileName=sys.argv[2];
else:
    print("Output file will be a.bin");

with open (inputFileName, "r") as myfile:
    intxt=myfile.readlines();

#
# parse code
#

outBinary=array.array('B');
dataSegmentBinary=array.array('B');

mp=megaParser();
try:
    mp.parse("".join(intxt)+"\n");
except:
    print("Exception parsing file:");
    print(sys.exc_info()[1]);
    sys.exit(1);

dsBaseAddress=mp.spitBinary(outBinary,dataSegmentBinary);

lnk=linker(dsBaseAddress);
lnk.link(outputFileName,outBinary,dataSegmentBinary,mp.dataLabelsArray,mp.dataLabelPostprocArr);

print("Done");

"""
l=[];
for a in range(0,256):
    b=math.fabs((127*math.sin(math.pi*a*2/256))+128);
    l.append(int(b));

print(l);
"""
