use os::Svm;
use std::env::args;
use std::fs::read;

unsafe extern "C" fn op_syscall(svm: *mut Svm) {
    syscall(&mut *svm);
    (*svm).ip += 1;
}
fn syscall(svm: &mut Svm) {
    println!("Bytecode length: {}", svm.size);
    println!("Value of #1: {}", svm.get_int_reg(1));
    svm.registers[1].content.integer = svm.get_int_reg(1) * 2;
    println!("Value of #1: {}", svm.get_int_reg(1));
}

fn main() {
    for arg in args().skip(1) {
        let contents: &[u8] = &read(arg).expect("Failed to read file");
        let svm: &mut Svm = Svm::new(contents, 200);
        svm.opcodes[0x52] = Some(op_syscall);
        Svm::run(svm);
        Svm::free(svm);
    }
}
