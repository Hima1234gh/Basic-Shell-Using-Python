import sys

def path_found(cmd) -> str:
    if path := shutil.which(cmd):
        return f"{cmd} is {path}" 
    else :
        return f{cmd}: 

BULITINS = {
    "exit" : lambda code=0, *_ : sys.exit(int(code)),
    "echo" : lambda *args : print(" ".join(args)),
    "type" : lambda cmd=None, *_: print(f"{cmd} is a shell builtin") if cmd in BULITINS else 
}

def main():
    while True :
        sys.stdout.write("$ ")
        sys.stdout.flush()
        user_input = input().split()

        if not user_input: 
            continue
        cmd,*args = user_input

        if cmd in BULITINS :
            BULITINS[cmd](*args)
        else :
            print(f"{cmd}: command not found")
        

if __name__ == "__main__":
    main()
