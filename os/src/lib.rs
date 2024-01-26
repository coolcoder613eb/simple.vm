#![allow(non_upper_case_globals)]
#![allow(non_camel_case_types)]
#![allow(non_snake_case)]
pub mod bindings {
    include!(concat!(env!("OUT_DIR"), "/bindings.rs"));
}
use bindings::{svm_free as _svm_free, svm_new as _svm_new, svm_run as _svm_run};

pub use bindings::svm_t as Svm;
pub fn svm_new(code: &[u8], memsize: u32) -> *mut Svm {
    let pcode: *mut u8 = code.as_ptr() as *mut u8;
    unsafe {
        let svm: *mut Svm = _svm_new(pcode, memsize);
        svm
    }
}
pub fn svm_run(svm: *mut Svm) {
    unsafe {
        _svm_run(svm);
    }
}

pub fn svm_free(svm: *mut Svm) {
    unsafe {
        _svm_free(svm);
    }
}
