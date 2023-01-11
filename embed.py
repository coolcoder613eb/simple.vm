import ctypes
from ctypes import *
import ctypes.util
import os
import sys


def run_vm(program):
    try:
        path = ctypes.util.find_library("simple-vm")
        assert path
        assert not os.path.isfile(os.path.join(os.getcwd(),path))
    except:
        path = ctypes.util.find_library(os.path.join(os.getcwd(),"simple-vm"))
        if not path:
            print('Could not find simple-vm DLL!')
            return
    program = list(program)
    vm = CDLL(path)
    #hwlist = [48, 1, 13, 0, 72, 101, 108, 108, 111, 44, 32, 87, 111, 114, 108, 100, 33, 49, 1]
    #arr19 = c_ubyte * 19
    #hw = arr19(*hwlist)
    size = len(program)
    Bytecode = c_ubyte * size
    prog = Bytecode(*program)

    REGISTER_COUNT = 10


    class RegContent(Union):
        _fields_ = [("integer", c_uint), ("string", c_char_p)]

    class Reg(Structure):
        _fields_ = [("content", RegContent), ("type", c_int)]

    class Flag(Structure):
        _fields_ = [("z", c_short)]

    class RegArr(Array):
        _length_ = REGISTER_COUNT
        _type_ = Reg

    class Svm(Structure):
        _fields_ = [("registers", RegArr),
                    ("flags", Flag),
                    ("ip", c_uint),
                    ("code", c_char_p),
                    ("size", c_uint),
                    ("error_handler",c_void_p),
                    ("opcodes", c_void_p * 256),
                    ("stack", c_int * 1024),
                    ("SP", c_int),
                    ("running", c_short)]



    vm.svm_new.restype = POINTER(Svm)
    cpu = vm.svm_new(prog,size)
    vm.svm_run(cpu)
    vm.svm_free(cpu)
