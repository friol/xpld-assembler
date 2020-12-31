#
# xpld - linker
# friol 2k20
#

class linker:

    def __init__(self,dsBaseAddress):
        
        self.dataSegmentBaseAddress=dsBaseAddress;

    def putRealAddress(self,outarr,pic,realaddr):

        assert outarr[pic+0]==0xb0;

        outarr[pic+0]=realaddr&0xff;
        outarr[pic+1]=(realaddr>>8)&0xff;
        outarr[pic+2]=(realaddr>>16)&0xff;
        outarr[pic+3]=(realaddr>>24)&0xff;

    def link(self,outFname,codeBinary,dataSegmentBinary,dataLabelsArray,dataLabelPostprocArray):

        # implant baseAddress+labelAddress into code binary

        for instr in dataLabelPostprocArray:
            #print(instr);
            for dataLab in dataLabelsArray:
                if instr[1]==dataLab[0]:
                    self.putRealAddress(codeBinary,instr[0],dataLab[3]+self.dataSegmentBaseAddress);

        # output final binary

        binaryHeader="XPLD0002";
        codeSize="CODESIZE";
        codeSegHeader="CODESEGM";
        dataSegBaseAddr="DSBASEDR";
        dataSegHeader="DATASEGM";

        outFile=open(outFname,"wb");

        my_str_as_bytes = str.encode(binaryHeader);
        outFile.write(bytearray(my_str_as_bytes));

        my_str_as_bytes = str.encode(codeSize);
        outFile.write(bytearray(my_str_as_bytes));

        cs=len(codeBinary);
        packedInt=[];
        for i in range(0,4):
            packedInt.append((cs>>(i*8))&0xff);
        for c in packedInt:
            outFile.write(c.to_bytes(1,'big'));

        my_str_as_bytes = str.encode(codeSegHeader);
        outFile.write(bytearray(my_str_as_bytes));

        barr=bytearray(codeBinary);
        outFile.write(barr);

        my_str_as_bytes = str.encode(dataSegBaseAddr);
        outFile.write(bytearray(my_str_as_bytes));

        packedInt=[];
        for i in range(0,4):
            packedInt.append((self.dataSegmentBaseAddress>>(i*8))&0xff);
        for c in packedInt:
            outFile.write(c.to_bytes(1,'big'));

        my_str_as_bytes = str.encode(dataSegHeader);
        outFile.write(bytearray(my_str_as_bytes));

        barr=bytearray(dataSegmentBinary);
        outFile.write(barr);
