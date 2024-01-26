use os::{svm_free, svm_new, svm_run, Svm};
use std::env::args;
use std::fs::read;

fn main() {
    for arg in args().skip(1) {
        let contents: &[u8] = &read(arg).expect("Failed to read file");
        let svm: *mut Svm = svm_new(contents, 200);
        svm_run(svm);
        svm_free(svm);
    }
}
