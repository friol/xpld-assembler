#
# xpld
# parser module
#

import sys;
import array;
import struct;
from lark import Lark,Token,Tree;

class genericException(Exception):
    pass;

class megaParser:

    def __init__(self):

        self.parsedTree=None;
        self.codePointer=0;
        self.labelPostprocArr=[];

        self.dataLabelsArray=[];
        self.dataLabelPostprocArr=[];

        self.listOfEquVars=[];

        self.codeBaseAddress=-1;
        self.dsBaseAddress=-1;

        self.instrDict={
            'hlt':0x00,
            'nop':0x01,
            'ld':0x10,
            'and':0x20,
            'add':0x30,
            'mul':0x32,
            'sub':0x40,
            'div':0xb0,
            'push':0x50,
            'cmp':0x60,
            'mod':0x70,
            'jmp':0x80,
            'jsr':0x90,
            'rts':0x91,
            'shr':0xa0,
            'shl':0xa2
            };

    #
    # main parser and grammar
    #

    def parse(self,txt):
        larkParser=Lark('''

        ?start: instruction+

        instruction: COMMENT _NEWLINE 
        | command _NEWLINE 
        | LABEL ":" _NEWLINE
        | DATALABEL DIMENSION datalist _NEWLINE
        | "." SUBROUTINE ":" _NEWLINE
        | EQUVARIABLE "equ" EQUVALUE
        | _NEWLINE
        
        COMMENT: /#.*/

        EQUVARIABLE: /\?[A-Z0-9]+/

        EQUVALUE: DECIMALNUMBER|HEXNUMBER

        LABEL: /@@[a-zA-Z0-9]+/

        SUBROUTINE: /[a-zA-Z][a-zA-Z0-9]+/

        DIMENSION: "db" | "dw" | "dd" | "ds"

        datalist: [DECIMALNUMBER ("," DECIMALNUMBER)*]
        | ESCAPED_STRING

        QUOTES: "\\""
        _STRING_INNER: /[a-zA-Z0-9\.()*\?:\-# ]+/
        ESCAPED_STRING : QUOTES _STRING_INNER QUOTES

        command: NOP_INSTR
        | HLT_INSTR
        | LD_INSTR  [argument ("," argument)*]
        | AND_INSTR [argument ("," argument)*] 
        | MOD_INSTR [argument ("," argument)*] 
        | ADD_INSTR [argument ("," argument)*] 
        | CMP_INSTR [argument ("," argument)*] 
        | SUB_INSTR [argument ("," argument)*] 
        | MUL_INSTR [argument ("," argument)*] 
        | SHR_INSTR [argument ("," argument)*] 
        | SHL_INSTR [argument ("," argument)*] 
        | DIV_INSTR [argument ("," argument)*] 
        | PUSH_INSTR REGISTERNAME
        | POP_INSTR REGISTERNAME
        | JNZ_INSTR LABEL
        | JZ_INSTR LABEL
        | JMP_INSTR LABEL
        | JMP_INSTR HEXNUMBER
        | JSR_INSTR HEXNUMBER
        | JSR_INSTR SUBROUTINE
        | RTS_INSTR
        | ORGCODE_INSTR HEXNUMBER
        | ORGDS_INSTR HEXNUMBER

        argument: REGISTERNAME | DECIMALNUMBER | HEXNUMBER | ABSOLUTE_ADDRESS | RELATIVE_ADDRESS | DATALABEL | EQUVARIABLE

        NOP_INSTR: "nop"
        HLT_INSTR: "hlt"
        LD_INSTR: "ld32" | "ld8" | "ld"
        AND_INSTR: "and"
        ADD_INSTR: "add"
        CMP_INSTR: "cmp"
        JMP_INSTR: "jmp"
        JNZ_INSTR: "jnz"
        JZ_INSTR: "jz"
        JSR_INSTR: "jsr"
        RTS_INSTR: "rts"
        SUB_INSTR: "sub"
        MUL_INSTR: "mul"
        MOD_INSTR: "mod"
        PUSH_INSTR: "push"
        POP_INSTR: "pop"
        SHR_INSTR: "shr"
        SHL_INSTR: "shl"
        DIV_INSTR: "div"
        ORGCODE_INSTR: "ORGCODE"
        ORGDS_INSTR: "ORGDS"

        REGISTERNAME: "r10" | "r11" | "r12" | "r13" | "r14" | "r15" | "r0" | "r1" | "r2" | "r3" | "r4" | "r5" | "r6" | "r7" | "r8" | "r9"

        DATALABEL: /[a-zA-Z0-9]+/

        DECIMALNUMBER: /[0-9]+/

        HEXNUMBER: "0x" /[0-9a-f]+/

        ABSOLUTE_ADDRESS: "[" HEXNUMBER "]"

        RELATIVE_ADDRESS: "[" REGISTERNAME "]"

        %import common.NEWLINE -> _NEWLINE
        %import common.WORD
        %ignore " "
        ''');

        self.parsedTree=larkParser.parse(txt);

    #
    # output 32-bit number to file
    #

    def spit32bitNumber(self,n,outarr):
        packedInt=[];
        for i in range(0,4):
            packedInt.append((n>>(i*8))&0xff);
        for c in packedInt:
            outarr.append(c);
        self.codePointer+=4;

    #
    # get equvariable value
    #

    def getEquvariableValue(self,equvar):
        for v in self.listOfEquVars:
            if equvar==v[0]:
                return v[1];

        raise "Equvariable not found";

    #
    # evaluate ld instruction
    #

    def evaluateLd(self,i1,i2,outarr,ldname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert (i1.children[0].type=="REGISTERNAME" or i1.children[0].type=="ABSOLUTE_ADDRESS" or i1.children[0].type=="RELATIVE_ADDRESS");

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;
            elif i2.children[0].type=="ABSOLUTE_ADDRESS":
                if ldname=="ld":
                    opcodeAdder=2;
                elif ldname=="ld8":
                    opcodeAdder=8;
            elif i2.children[0].type=="DATALABEL":
                if ldname=="ld":
                    opcodeAdder=9;
            elif i2.children[0].type=="RELATIVE_ADDRESS":
                if ldname=="ld8":
                    opcodeAdder=0xa;
                elif ldname=="ld32":
                    opcodeAdder=0xd;

        elif i1.children[0].type=="ABSOLUTE_ADDRESS":
            if ldname=="ld32":
                if i2.children[0].type=="REGISTERNAME":
                    opcodeAdder=3;
                elif i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                    opcodeAdder=5;
            elif ldname=="ld8":
                if i2.children[0].type=="REGISTERNAME":
                    opcodeAdder=4;
                elif i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                    opcodeAdder=6;
        elif i1.children[0].type=="RELATIVE_ADDRESS":
            if ldname=="ld8":
                if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                    opcodeAdder=0xc;
                else:
                    opcodeAdder=7;
            elif ldname=="ld32":
                if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                    opcodeAdder=0xe;
                else:
                    opcodeAdder=0xb;
            else:
                opcodeAdder=0xb;

        # spit out opcode
        outarr.append(self.instrDict['ld']+opcodeAdder);
        self.codePointer+=1;

        # spit out destination register/address
        if i1.children[0].type=="REGISTERNAME":
            outarr.append(int(destReg[1:]));
            self.codePointer+=1;
        elif i1.children[0].type=="ABSOLUTE_ADDRESS":
            addr=i1.children[0].replace("[","").replace("]","");
            finalVal=int(addr,16);
            self.spit32bitNumber(finalVal,outarr);
        elif i1.children[0].type=="RELATIVE_ADDRESS":
            reg=i1.children[0].replace("[r","").replace("]","");
            outarr.append(int(reg));
            self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER","EQUVARIABLE"]:
            finalVal=0;

            if i2.children[0].type=="EQUVARIABLE":
                val=self.getEquvariableValue(i2.children[0]);
            else:
                val=i2.children[0];

            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            if ldname=="ld32" or ldname=="ld":
                self.spit32bitNumber(finalVal,outarr);
            elif ldname=="ld8":
                outarr.append(finalVal&0xff);
                self.codePointer+=1;
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;
        elif i2.children[0].type=="ABSOLUTE_ADDRESS":
            addr=i2.children[0].replace("[","").replace("]","");
            finalVal=int(addr,16);
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="DATALABEL":
            #print("ld to datalabel "+str(opcodeAdder)+" "+str(i2.children[0].value));
            self.dataLabelPostprocArr.append([len(outarr),i2.children[0].value]);
            self.spit32bitNumber(0xb0b0b0b0,outarr);
        elif i2.children[0].type=="RELATIVE_ADDRESS":
            reg=i2.children[0].replace("[r","").replace("]","");
            outarr.append(int(reg));
            self.codePointer+=1;


        return True;

    #
    # evaluate and instruction
    #

    def evaluateAnd(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['and']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate mod instruction
    #

    def evaluateMod(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['mod']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate add instruction
    #

    def evaluateAdd(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['add']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate shr instruction
    #

    def evaluateShr(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['shr']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate shl instruction
    #

    def evaluateShl(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['shl']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate mul instruction
    #

    def evaluateMul(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['mul']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER","EQUVARIABLE"]:

            finalVal=0;

            if i2.children[0].type=="EQUVARIABLE":
                val=self.getEquvariableValue(i2.children[0]);
            else:
                val=i2.children[0];

            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate div instruction
    #

    def evaluateDiv(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['div']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate sub instruction
    #

    def evaluateSub(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['sub']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id (or relative address)
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
            finalVal=0;
            val=i2.children[0];
            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # evaluate cmp instruction
    #

    def evaluateCmp(self,i1,i2,outarr,addname):

        opcodeAdder=0;

        assert i1.data=="argument";
        assert i2.data=="argument";

        assert i1.children[0].type=="REGISTERNAME";

        if i1.children[0].type=="REGISTERNAME":
            destReg=i1.children[0];
            assert destReg in ["r0","r1","r2","r3","r4","r5","r6","r7","r8","r9","r10","r11","r12","r13","r14","r15"];

            if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER"]:
                opcodeAdder=0;
            elif i2.children[0].type=="REGISTERNAME":
                opcodeAdder=1;

        # spit out opcode
        outarr.append(self.instrDict['cmp']+opcodeAdder);
        self.codePointer+=1;

        #spit out dest register id
        outarr.append(int(destReg[1:]));
        self.codePointer+=1;

        # spit out arguments
        if i2.children[0].type in ["DECIMALNUMBER","HEXNUMBER","EQUVARIABLE"]:
            finalVal=0;

            if i2.children[0].type=="EQUVARIABLE":
                val=self.getEquvariableValue(i2.children[0]);
            else:
                val=i2.children[0];

            try:
                if val[0:2]=="0x":
                    finalVal=int(val,16);
                else:
                    finalVal=int(val);
                #print("Spitting out 32bit value for "+str(finalVal));
            except:
                print("Unable to parse as number value ["+val+"]");
                return False;
            self.spit32bitNumber(finalVal,outarr);
        elif i2.children[0].type=="REGISTERNAME":
            srcReg=i2.children[0];
            outarr.append(int(srcReg[1:]));
            self.codePointer+=1;

        return True;

    #
    # jmp instructions and rts
    #

    def evaluateJmp(self,i1,outarr):

        opcodeAdder=0;
        if i1.type=="HEXNUMBER":
            opcodeAdder=2;

        # spit out opcode
        outarr.append(self.instrDict['jmp']+opcodeAdder);
        self.codePointer+=1;

        if i1.type=="LABEL":
            # spit out fake 4bytes address and store it for postprocessing
            self.labelPostprocArr.append([len(outarr),i1.value]);
            self.spit32bitNumber(0xa0a0a0a0,outarr);
        else:
            self.spit32bitNumber(int(i1.value,16),outarr);

        return True;        

    def evaluateJnz(self,i1,outarr):

        # spit out opcode
        outarr.append(self.instrDict['jmp']+1);
        self.codePointer+=1;

        # spit out fake 4bytes address and store it for postprocessing
        self.labelPostprocArr.append([len(outarr),i1.value]);
        self.spit32bitNumber(0xa0a0a0a0,outarr);

        return True;

    def evaluateJz(self,i1,outarr):

        # spit out opcode
        outarr.append(self.instrDict['jmp']+3);
        self.codePointer+=1;

        # spit out fake 4bytes address and store it for postprocessing
        self.labelPostprocArr.append([len(outarr),i1.value]);
        self.spit32bitNumber(0xa0a0a0a0,outarr);

        return True;

    def evaluateJsr(self,i1,outarr):

        opcodeAdder=0;
        if i1.type=="HEXNUMBER":
            opcodeAdder=2;

        # spit out opcode
        outarr.append(self.instrDict['jsr']+opcodeAdder);
        self.codePointer+=1;

        if i1.type=="SUBROUTINE":
            # spit out fake 4bytes address and store it for postprocessing
            self.labelPostprocArr.append([len(outarr),i1.value]);
            self.spit32bitNumber(0xc0c0c0c0,outarr);
        else:
            self.spit32bitNumber(int(i1.value,16),outarr);

        return True;        

    #
    # complete jumps with correct jump address
    #

    def putRealAddress(self,outarr,pic,realaddr):

        assert outarr[pic+0]==0xa0 or outarr[pic+0]==0xc0;

        outarr[pic+0]=realaddr&0xff;
        outarr[pic+1]=(realaddr>>8)&0xff;
        outarr[pic+2]=(realaddr>>16)&0xff;
        outarr[pic+3]=(realaddr>>24)&0xff;

    def implantJumpAddress(self,codeElement,labelList,outarr):

        implanted=False;
        for lab in labelList:
            if lab[0]==codeElement[1]:
                pointInCode=codeElement[0];
                realAddress=lab[1]+self.codeBaseAddress;

                self.putRealAddress(outarr,pointInCode,realAddress);
                implanted=True;

        if not implanted:
            raise genericException("Error: couldn't find address for label "+str(codeElement));


    #
    # output opcode
    #

    def spitInstruction(self,instr,outBinArr):
        
        assert type(instr[0])==Token;
        #print(instr[0].type);

        if instr[0].type=="HLT_INSTR":
            outBinArr.append(self.instrDict["hlt"]);
            self.codePointer+=1;
        elif instr[0].type=="NOP_INSTR":
            outBinArr.append(self.instrDict["nop"]);
            self.codePointer+=1;
        elif instr[0].type=="LD_INSTR":
            if not self.evaluateLd(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="AND_INSTR":
            if not self.evaluateAnd(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="MOD_INSTR":
            if not self.evaluateMod(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="ADD_INSTR":
            if not self.evaluateAdd(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="SHR_INSTR":
            if not self.evaluateShr(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="SHL_INSTR":
            if not self.evaluateShl(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="DIV_INSTR":
            if not self.evaluateDiv(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="MUL_INSTR":
            if not self.evaluateMul(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="SUB_INSTR":
            if not self.evaluateSub(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="CMP_INSTR":
            if not self.evaluateCmp(instr[1],instr[2],outBinArr,instr[0]):
                sys.exit(1);
        elif instr[0].type=="JNZ_INSTR":
            if not self.evaluateJnz(instr[1],outBinArr):
                sys.exit(1);
        elif instr[0].type=="JZ_INSTR":
            if not self.evaluateJz(instr[1],outBinArr):
                sys.exit(1);
        elif instr[0].type=="JMP_INSTR":
            if not self.evaluateJmp(instr[1],outBinArr):
                sys.exit(1);
        elif instr[0].type=="JSR_INSTR":
            if not self.evaluateJsr(instr[1],outBinArr):
                sys.exit(1);
        elif instr[0].type=="RTS_INSTR":
            outBinArr.append(self.instrDict["rts"]);
            self.codePointer+=1;
        elif instr[0].type=="PUSH_INSTR":
            outBinArr.append(self.instrDict["push"]);
            regNum=int(str(instr[1]).replace("r",""));
            outBinArr.append(regNum);
            self.codePointer+=2;
        elif instr[0].type=="POP_INSTR":
            outBinArr.append(self.instrDict["push"]+1);
            regNum=int(str(instr[1]).replace("r",""));
            outBinArr.append(regNum);
            self.codePointer+=2;
        elif instr[0].type=="ORGCODE_INSTR":
            self.codeBaseAddress=int(instr[1],16);
        elif instr[0].type=="ORGDS_INSTR":
            self.dsBaseAddress=int(instr[1],16);

    #
    # add data label to list
    #

    def addDataLabel(self,el):

        assert el.data=="instruction";

        labelName=el.children[0];
        dimension=el.children[1];

        valList=[];

        if el.children[1]=="ds":
            sttrr=el.children[2].children[0].replace("\"","");
            for c in sttrr:
                valList.append(ord(c));
            valList.append(0); # strings are zero terminated
        else:
            for i in el.children[2].children:
                valList.append(int(i));

        self.dataLabelsArray.append([labelName,dimension,valList]);

    # 
    # create binary for data segment
    #

    def createDataSegment(self,outDataSegBin):

        baseAddr=0;
        for el in self.dataLabelsArray:
            #print(el);
            if el[1] in ["db","ds"]:
                for b in el[2]:
                    outDataSegBin.append(b);
                el.append(baseAddr);
                baseAddr+=len(el[2]);
            elif el[1]=="dd":
                for dw in el[2]:
                    packedInt=[];
                    for i in range(0,4):
                        packedInt.append((dw>>(i*8))&0xff);
                    for c in packedInt:
                        outDataSegBin.append(c);
                el.append(baseAddr);
                baseAddr+=len(el[2])*4;


    #
    # output compiled code
    #

    def spitBinary(self,outBinArr,outDataSegment):

        # tree root must be a start
        assert self.parsedTree.data=="start";

        # list of labels
        labelList=[];

        for el in self.parsedTree.children:
            #print(el);
            
            assert el.data=="instruction";
            instrCore=el.children;

            if len(instrCore)==0:
                # empty line
                pass;
            elif type(instrCore[0])==Token:
                # token can be a comment or a label or a datalabel or an equlabel
                if instrCore[0].type=="LABEL":
                    #print("Label:"+instrCore[0]+" code position:"+str(self.codePointer));
                    labelList.append([instrCore[0].value,self.codePointer]);
                elif instrCore[0].type=="DATALABEL":
                    self.addDataLabel(el);
                elif instrCore[0].type=="SUBROUTINE":
                    labelList.append([instrCore[0].value,self.codePointer]);
                elif instrCore[0].type=="EQUVARIABLE":
                    varName=instrCore[0].value;
                    varValue=instrCore[1].value;
                    self.listOfEquVars.append([varName,varValue]);
            elif type(instrCore[0]==Tree):
                # tree can be a command
                assert instrCore[0].data=="command";
                self.spitInstruction(instrCore[0].children,outBinArr);

        if self.codeBaseAddress==-1 or self.dsBaseAddress==-1:
            raise("Error: no ORGCODE or ORGDS directives in code");

        print("Code base address will be "+str(hex(self.codeBaseAddress)));
        print("Data segment base address will be "+str(hex(self.dsBaseAddress)));

        #print(self.dataLabelsArray);

        for el in self.labelPostprocArr:
            self.implantJumpAddress(el,labelList,outBinArr);

        #print(self.dataLabelPostprocArr);

        # create data segment with data
        self.createDataSegment(outDataSegment);
        #print(self.dataLabelsArray);

        return self.dsBaseAddress;

    #
    # preprocess includes
    #

    def preprocessIncludes(self,intxt):

        resultingArray=[];

        for l in intxt:
            if l=="\n":
                pass;
            else: 
                #l=l[:-1];
                larr=l.split(" ");
                if (larr[0]=="include"):
                    if len(larr)!=2:
                        print("Syntax error at include statement");
                        raise genericException("Syntax error at include statement");
                    else:
                        fname=larr[1][:-1];
                        with open (fname, "r") as myfile:
                            includeText=myfile.readlines();
                        for line in includeText:
                            resultingArray.append(line);
                else:
                    resultingArray.append(l);

        return resultingArray;
