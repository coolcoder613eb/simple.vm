from cffi import FFI

HEADER='''
typedef struct registers {
    union {
        unsigned int integer;
        char *string;
    } content;
    enum { INTEGER, STRING } type;
} reg_t;
typedef struct flags {
    short z;
} flag_t;
struct svm;
typedef void opcode_implementation(struct svm *in);
typedef struct svm {
    reg_t registers[10];
    flag_t flags;
    unsigned int ip;
    unsigned char *code;
    unsigned int size;
    void (*error_handler) (char *msg);
    opcode_implementation *opcodes[256];
    int stack[1024];
    int SP;
    short running;
} svm_t;
svm_t *svm_new(unsigned char *code, unsigned int size);
void svm_set_error_handler(svm_t * cpup, void (*fp) (char *msg));
void svm_default_error_handler(svm_t * cpup, char *msg);
void svm_dump_registers(svm_t * cpup);
void svm_free(svm_t * cpup);
void svm_run(svm_t * cpup);
void svm_run_N_instructions(svm_t * cpup, int max_instructions);
'''

ffi = FFI()
ffi.cdef(HEADER)
ffi.set_source("simple_vm",
"""
     #include "simple-vm.h"   // the C header of the library
""",
     library_dirs=['..'], libraries=['simple-vm'])   # library name, for the linker
ffi.compile(verbose=True)
