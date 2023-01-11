import builtins as blt
#
# This is a simple compiler which will read an input file
# and spit out the corresponding bytecodes for the program.
#
# The only real complexity comes from having to account for labels
# as our virtual machine only understands absolute jumps.
#
#      e.g. Rather than "jmp $+3", or "jmp $-8" we can only write
#           "jump address", where "address" is an integer 0-64k.
#
# To cope with this we initially write all jump-targets as
# "JMP 0x0000" and keep track of the length of each instruction
# we've generated.
#
# After the whole program has been compiled we can go back and fill
# in the absolute/real destination for the jumps.
#
# Not ideal, but it is simpler than either parsing for-real or
# using a multi-pass parser.

#
#  These are the bytecodes we understand.
#
EXIT = 0x00

#
#  Integer things.
#
INT_STORE = 0x01
INT_PRINT = 0x02
INT_TOSTRING = 0x03
INT_RANDOM = 0x04

#
#  Jumps
#
JUMP_TO = 0x10
JUMP_Z = 0x11
JUMP_NZ = 0x12


#
#  Mathematical
#
XOR_OP = 0x20
ADD_OP = 0x21
SUB_OP = 0x22
MUL_OP = 0x23
DIV_OP = 0x24
INC_OP = 0x25
DEC_OP = 0x26
AND_OP = 0x27
OR_OP = 0x28


#
#  String operations
#
STRING_STORE = 0x30
STRING_PRINT = 0x31
STRING_CONCAT = 0x32
STRING_SYSTEM = 0x33
STRING_TOINT = 0x34
STRING_IN = 0x35


#
#  Comparison functions
CMP_REG = 0x40
CMP_IMMEDIATE = 0x41
CMP_STRING = 0x42
IS_STRING = 0x43
IS_INTEGER = 0x44

#  Misc things
NOP_OP = 0x50
REG_STORE = 0x51

#  Load from RAM/store in RAM
PEEK = 0x60
POKE = 0x61
MEMCPY = 0x62

#  Stack operations
STACK_PUSH = 0x70
STACK_POP = 0x71
STACK_RET = 0x72
STACK_CALL = 0x73


#
#  Get the input file we'll parse
#
import sys

for file in sys.argv[1:]:

    #
    #  Storage for any labels we find in the source-file.
    #
    LABELS = {}


    #
    #  This stores the offsets we need to update when we've finished
    # compiling the source.
    #
    #  Every time we see a "JUMP $label" statement we output JMP 0x0000
    # and once the input has been completely parsed we will then go back
    # and update the output with the real destinations.
    #
    #  See the header for more discussion on this topic.
    #
    UPDATES = []


    # Output/compiled programs will have a .raw suffix.
    output = file.rsplit('.', 1)[0] + ".raw"


    #
    #  Open our input/output files.
    #
    with open(file, 'r') as in_file:
        with open(output, 'wb') as out_file:
        
            #
            #  Amount of instructions we've output.
            #
            #  As instructions aren't the same lengths we need to
            # ensure we keep track of them so we can calculate jumping
            # offsets.
            #
            offset = 0
            
            #
            #  Process each line of the input
            #
            for line in in_file:
                
                #print(UPDATES)
            
                #
                #  Except comments / empty lines.
                #
                line = line.strip()
                if not line or line.startswith(';') or line.startswith('#'):
                    #print('com')
                    continue
                else:
                    #print(line.removesuffix('\n'))
                    pass


                #
                #  Label definition ":foo"
                #
                if line.startswith(':'):
                    name = line[1:]
                    
                    # Ensure labels are unique.
                    if name in LABELS:
                        print("WARNING: Label name '{}' defined multiple times!\n".format(name))
                        print("         Picking first occurrence.\n")
                        print("         This is probably your bug.\n")
                    
                    #
                    #  If a label starts with "0x" or is entirely numeric it
                    # WILL be confused for an address.
                    #
                    if name.startswith('0x') or name.isdigit():
                        print("WARNING: Label named '{}' WILL be confused for an address\n".format(name))
                        print("         Strongly consider changing this\n")
                    
                    #
                    # Store the current location of the code in the label.
                    #
                    # We can do this safely because each generator keeps track
                    # of how long and instruction is.
                    #
                    LABELS[name] = offset
                elif line.startswith('store #') and line.count('"') == 2:
                
                    # store a string
                    #str = line[''.join((x if x != '"' else break) for x in line[line.index('"'):])]#.split('"')
                    str = ''
                    isstr = False
                    for x in line:
                        if x == '"':
                            isstr = not isstr
                            continue
                        if isstr:
                            str += x
                    #print('str = '+str)
                    #print(line.split('#'))
                    reg = blt.int(line.split('#')[1][0])
                    #str = str[1:-1]
                    
                    # expand newlines, etc.
                    str = str.replace('\\n', '\n').replace('\\t', '\t')
                    
                    len = blt.len(str)
                    
                    len1 = len % 256
                    len2 = (len - len1) // 256
                    
                    out_file.write(bytes([STRING_STORE]))
                    out_file.write(bytes([reg]))
                    out_file.write(bytes([len1]))
                    out_file.write(bytes([len2]))


                    out_file.write(str.encode())
                    
                    offset += 4              # store + reg + len
                    offset += blt.len(str)
                elif line.startswith('store #') and line.count('#') == 2:
                
                    # store a register contents with another
                    dest, src = line.split(', ')
                    dest = int(dest.split('#')[1])
                    src = int(src.split('#')[1])
                    
                    out_file.write(bytes([REG_STORE]))
                    out_file.write(bytes([dest]))
                    out_file.write(bytes([src]))
                    
                    offset += 3    # store + reg1 + reg2
                elif line.startswith('store #') and line.count('#') == 1:
                
                    # store a label address, or integer
                    #print(line.split(', ')[:2])
                    reg, val = line.split(', ')[0], ', '.join(line.split(', ')[1:])
                    reg = int(reg.split('#')[1])
                    
                    if val.startswith('0x') or val.isdigit():
                    
                        #
                        #  If the value is entirely numeric, or starts with 0x
                        # then it is an integer.
                        #
                        val = int(val, 16) if val.startswith('0x') else int(val)
                        
                        if val > 65535:
                            raise Exception("Int too large")
                        
                        val1 = val % 256
                        val2 = (val - val1) // 256
                        
                        out_file.write(bytes([INT_STORE]))
                        out_file.write(bytes([reg]))
                        out_file.write(bytes([val1]))
                        out_file.write(bytes([val2]))
                        offset += 4    # store + reg + len
                    else:
                    
                        #
                        # Storing the address of a label.
                        #
                        out_file.write(bytes([INT_STORE]))
                        out_file.write(bytes([reg]))
                        out_file.write(bytes([0x00]))
                        out_file.write(bytes([0x00]))
                        
                        offset += 4    # store + reg + len
                        
                        UPDATES.append({'offset': (offset - 2), 'label': val})
                elif line.startswith('exit'):
                    out_file.write(bytes([EXIT]))
                    offset += 1
                elif line.startswith('nop'):
                    out_file.write(bytes([NOP_OP]))
                    offset += 1
                elif line.startswith('print_int #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([INT_PRINT]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('print_str #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STRING_PRINT]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('in_str #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STRING_IN]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('system #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STRING_SYSTEM]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('goto ') or line.startswith('jmp ') or line.startswith('jmpz ') or line.startswith('jmpnz ') or line.startswith('call '):
                
                    # jump/call
                    type, dest = line.split(' ')
                    types = {'goto': JUMP_TO, 'jmp': JUMP_TO, 'jmpz': JUMP_Z, 'jmpnz': JUMP_NZ, 'call': STACK_CALL}
                    
                    #
                    #  If the destination begins with 0x or is entirely numeric
                    # then it is an address - otherwise a label.
                    #
                    if dest.startswith('0x') or dest.isdigit():
                    
                        dest = int(dest, 16) if dest.startswith('0x') else int(dest)
                        a1 = dest % 256
                        a2 = (dest - a1) // 256
                        
                        out_file.write(bytes([types[type]]))
                        out_file.write(bytes([a1]))
                        out_file.write(bytes([a2]))
                        offset += 3    # jump + val1 + val2
                    
                    else:
                        out_file.write(bytes([types[type]]))
                        
                        out_file.write(bytes([0]))    # this will be updated.
                        out_file.write(bytes([0]))    # this will be updated.
                        
                        offset += 3        # jump + val1 + val2
                        
                        #
                        # we now need to record the fact we have to patch up this
                        # instruction.
                        #
                        #print({'offset': (offset - 2), 'label': dest})
                        UPDATES.append({'offset': (offset - 2), 'label': dest})
                elif line.startswith('add #') or line.startswith('and #') or line.startswith('or #') or line.startswith('sub #') or line.startswith('mul #') or line.startswith('div #') or line.startswith('xor #') or line.startswith('concat #'):
                
                    #
                    #  Each of these operations compiles to code of the form:
                    #
                    #   OPERATION Result-Register, SrcReg1, SrcReg2
                    #
                    maths = {'add': ADD_OP, 'and': AND_OP, 'or': OR_OP, 'sub': SUB_OP, 'mul': MUL_OP, 'div': DIV_OP, 'xor': XOR_OP, 'concat': STRING_CONCAT}
                    
                    opr = line.split()[0]
                    #reg = blt.int(line.split('#')[1][0])
                    dest = blt.int(line.split('#')[1][0])
                    src1 = blt.int(line.split('#')[2][0])
                    src2 = blt.int(line.split('#')[3][0])


                    out_file.write(bytes([maths[opr.lower()]]))
                    out_file.write(bytes([dest]))
                    out_file.write(bytes([src1]))
                    out_file.write(bytes([src2]))
                    
                    offset += 4    # op + dest + src1 + src2
                elif line.startswith('dec #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([DEC_OP]))
                    out_file.write(bytes([reg]))
                    
                    offset += 2
                elif line.startswith('inc #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([INC_OP]))
                    out_file.write(bytes([reg]))
                    
                    offset += 2
                elif line.startswith('int2string #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([INT_TOSTRING]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('random #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([INT_RANDOM]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('string2int #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STRING_TOINT]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('cmp #') and line.count('#') == 2:
                    reg1, reg2 = line.split(',')
                    reg1 = int(reg1.split('#')[1])
                    reg2 = int(reg2.split('#')[1])
                    
                    out_file.write(bytes([CMP_REG]))
                    out_file.write(bytes([reg1]))
                    out_file.write(bytes([reg2]))
                    
                    offset += 3
                elif line.startswith('cmp #') and line.count('"') == 2:
                
                    # compare a register with a string.
                    str = ''
                    isstr = False
                    for x in line:
                        if x == '"':
                            isstr = not isstr
                            continue
                        if isstr:
                            str += x
                    #print('str = '+str)
                    #print(line.split('#'))
                    reg = blt.int(line.split('#')[1][0])
                    #str = str[1:-1]
                    
                    # expand newlines, etc.
                    str = str.replace('\\n', '\n').replace('\\t', '\t')
                    
                    len = blt.len(str)
                    
                    len1 = len % 256
                    len2 = (len - len1) // 256
                    
                    out_file.write(bytes([CMP_STRING]))
                    out_file.write(bytes([reg]))
                    out_file.write(bytes([len1]))
                    out_file.write(bytes([len2]))
                    
                    out_file.write(str.encode())
                    
                    offset += 4              # cmp + reg + len
                    offset += blt.len(str)
                elif line.startswith('cmp #') and line.count('#') == 1:
                
                    # compare a register with an int - TODO: Label.
                    reg, val = line.split(',')
                    reg = int(reg.split('#')[1])
                    
                    # convert from hex if appropriate.
                    val = int(val, 16) if val.startswith('0x') else int(val)
                    
                    val1 = val % 256
                    val2 = (val - val1) // 256
                    
                    out_file.write(bytes([CMP_IMMEDIATE]))
                    out_file.write(bytes([reg]))
                    out_file.write(bytes([val1]))
                    out_file.write(bytes([val2]))
                    offset += 4    # cmp reg val1 val2
                elif line.startswith('is_string #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([IS_STRING]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('is_integer #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([IS_INTEGER]))
                    out_file.write(bytes([reg]))
                    offset += 2
                elif line.startswith('peek #') and line.count('#') == 2:
                    reg, addr = line.split(',')
                    reg = int(reg.split('#')[1])
                    addr = int(addr.split('#')[1])
                    
                    out_file.write(bytes([PEEK]))
                    out_file.write(bytes([reg]))
                    out_file.write(bytes([addr]))
                    
                    offset += 3
                elif line.startswith('poke #') and line.count('#') == 2:
                    reg, addr = line.split(',')
                    reg = int(reg.split('#')[1])
                    addr = int(addr.split('#')[1])
                    
                    out_file.write(bytes([POKE]))
                    out_file.write(bytes([reg]))
                    out_file.write(bytes([addr]))
                    offset += 3
                elif line.startswith('memcpy #') and line.count('#') == 3:
                    src, dst, len = line.split(',')
                    src = int(src.split('#')[1])
                    dst = int(dst.split('#')[1])
                    len = int(len.split('#')[1])
                    
                    out_file.write(bytes([MEMCPY]))
                    out_file.write(bytes([src]))
                    out_file.write(bytes([dst]))
                    out_file.write(bytes([len]))
                    
                    offset += 4
                elif line.startswith('push #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STACK_PUSH]))
                    out_file.write(bytes([reg]))
                    
                    offset += 2
                elif line.startswith('pop #'):
                    reg = int(line.split('#')[1])
                    
                    out_file.write(bytes([STACK_POP]))
                    out_file.write(bytes([reg]))
                    
                    offset += 2
                elif line.startswith('ret'):
                    out_file.write(bytes([STACK_RET]))
                    offset += 1
                elif line.startswith('db ') or line.startswith('data '):
                    data = line.split(' ')[1]
                    
                    #
                    #  Split each byte
                    #
                    for db in data.split(','):
                    
                        # strip leading/trailing space
                        db = db.strip()
                        
                        if not db:
                            continue
                        
                        # convert from hex if appropriate
                        db = int(db, 16) if db.startswith('0x') else int(db)
                        
                        # ensure the byte is within range.
                        if db > 255:
                            raise Exception("Data too large for a byte: {}".format(db))
                        
                        out_file.write(bytes([db]))
                        
                        offset += 1
                else:
                    print("WARNING UNKNOWN LINE: {}".format(line))


    if offset < 1:
        print("WARNING: Didn't generate any code")


    #
    #  Close the input/output files.
    #
    in_file.close()
    out_file.close()


    #
    #  OK now this is nasty - we want to go back and patch up the jump
    # instructions we know we've emitted.
    #
    #print(UPDATES)
    if blt.len(UPDATES) > 0:
    
        #
        #  Open for in-place editing and make sure we're at the right spot.
        #
        with open(output, 'r+b') as tmp:
        
            #
            #  For each update we must apply
            #
            for update in UPDATES:
            
                #
                # We have the offset in the output file to update, and the
                # label which should be replaced with the address.
                #
                offset = update['offset']
                label = update['label']
                
                #
                #  Seek to the correct location.
                #
                tmp.seek(offset, 0)
                
                #
                # now we find the target of the label
                #
                target = LABELS[label]
                if target is None:
                    raise Exception("No target for label '{}' - Label not defined!".format(label))
                
                #
                # Split the address into two bytes.
                #
                t1 = target % 256
                t2 = (target - t1) // 256
                
                #
                # Update the compiled file on-disk.  (Remember the seek?)
                #
                tmp.write(bytes([t1]))
                tmp.write(bytes([t2]))


        #
        # Close the updated output file.
        #
        tmp.close()
