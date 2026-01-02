import os
import sys
import shutil
import subprocess

#Finds the path in the given command
def path_found(cmd) -> str:
    if path := shutil.which(cmd):
        return f"{cmd} is {path}" 
    else :
        return f"{cmd}: not found"

#List of Built-in commands 
BULITINS = {
    "exit" : lambda code=0, *_ : sys.exit(int(code)), #Exits the shell with the given code
    "echo" : lambda *args : print(" ".join(args)), #Prints the arguments to the console
    "type" : lambda cmd=None, *_: print(f"{cmd} is a shell builtin") if cmd in BULITINS else print(path_found(cmd)), #Finds if the command is a built-in or external command
    "pwd" : lambda : print(subprocess.getoutput("pwd")), #Prints the current working directory
    "cd" : lambda path="~" : os.chdir(os.path.expanduser(path)) if os.path.exists(os.path.expanduser(path)) else print(f"cd: {path}: No such file or directory"), #Changes the current working directory
}


#Main function to run the shell
def main():
    while True : #Infinite loop to keep the shell running
        sys.stdout.write("$ ")
        sys.stdout.flush()
        user_input = input().split()

        if not user_input: #If no input is given, continue to the next iteration
            continue
        cmd,*args = user_input

        if cmd in BULITINS :
            BULITINS[cmd](*args) #Execute the built-in command
        else :
            try:
                subprocess.run([cmd] + args)
            except FileNotFoundError:
                print(f"{cmd}: command not found")
        

if __name__ == "__main__":
    main()
