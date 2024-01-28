#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
pub mod bindings {
    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}
use bindings::{
    registers_INTEGER, registers_STRING, svm_default_error_handler, svm_free as _svm_free,
    svm_new as _svm_new, svm_run as _svm_run,
};
use std::ffi::{CStr, CString};
use std::os::raw::c_char;

pub use bindings::svm_t as Svm;
impl Svm {
    pub fn new(code: &[u8], memsize: u32) -> &mut Svm {
        let pcode: *mut u8 = code.as_ptr() as *mut u8;
        unsafe {
            let svm: *mut Svm = _svm_new(pcode, memsize);
            &mut *svm
        }
    }
    pub fn run(&mut self) {
        unsafe {
            _svm_run(self);
        }
    }

    pub fn free(&mut self) {
        unsafe {
            _svm_free(self);
        }
    }
    pub fn get_int_reg(&mut self, reg: usize) -> u32 {
        if self.registers[reg].type_ == registers_INTEGER {
            unsafe {
                return self.registers[reg].content.integer;
            }
        }
        self.default_error_handler("The register doesn't contain an integer");
        0
    }
    pub fn get_string_reg(&mut self, reg: usize) -> &str {
        if self.registers[reg].type_ == registers_STRING {
            return unsafe { CStr::from_ptr(self.registers[reg].content.string) }
                .to_str()
                .unwrap();
        }
        self.default_error_handler("The register doesn't contain an string");
        ""
    }
    pub fn default_error_handler(&mut self, msg: &str) {
        let c_str = CString::new(msg).unwrap();
        let c_msg: *mut c_char = c_str.as_ptr() as *mut c_char;
        unsafe { svm_default_error_handler(self as *mut Self, c_msg) }
    }
}
