import sys
import os
from os.path import join, isfile
import embed
import subprocess
import shlex
EXT = '.raw'
PATH = os.environ['PATH'].split(os.pathsep)
PATH.append(join(os.getcwd(),''))

shell = subprocess.Popen('', stdin=subprocess.PIPE, stdout=subprocess.PIPE)

def runcmd(cmd):
    shell.stdin.write(cmd)
    return shell.stdin.read()


run = True
while run:
    ii = input(os.getcwd()+' % ') # " ? "
    si = shlex.split(ii)
    i = si[0]
    for x in PATH:
        xi = join(x,i)
        if (isfile(xi) and xi.endswith(EXT)) or isfile(xi+EXT):
            filename = xi if xi.endswith(EXT) else xi+EXT
            with open(filename,'rb') as f:
                program = f.read()
            print(filename)
            embed.run_vm(program)
    if i == 'exit':
        sys.exit()
    elif i == 'calc':
        t = input('>')
        while t != 'exit' and t != '\0':
            try:
                print(eval(t))
                t = input('>')
            except:
                break
