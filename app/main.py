import os
import sys
import shutil
import subprocess
import shlex
import re 

#Finds the path in the given command
def path_found(cmd) -> str:
    if path := shutil.which(cmd):
        return f"{cmd} is {path}" 
    else :
        return f"{cmd}: not found"

def expand_vars(arg: str) -> str:
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            return os.environ.get(var_name, "") 
        pattern = r'\$(\w+)|\${(\w+)}'
        return re.sub(pattern, replace_var, arg)


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
    while True : 
        try : #Infinite loop to keep the shell running
            sys.stdout.write("$ ")
            sys.stdout.flush()
            user_input = input()
            stdin = None
            try :
                tokens = shlex.split(user_input, posix=True) #Parse the input using shlex
                
            except ValueError as ve:
                print(f"Error parsing input: {ve}")
                continue

            if "<" in tokens:
                    idx = tokens.index("<")

                    # Syntax validation
                    if idx == len(tokens) - 1:
                        print("syntax error: expected filename after '<'")
                        continue

                    infile = tokens[idx + 1]

                    try:
                        stdin = open(infile, "r")
                    except FileNotFoundError:
                        print(f"{infile}: No such file or directory")
                        continue
                    except PermissionError:
                        print(f"{infile}: Permission denied")
                        continue

                    # Remove '< file'
                    del tokens[idx:idx + 2]



            if not user_input: #If no input is given, continue to the next iteration
                continue

            expanded = [expand_vars(arg) for arg in tokens]#Expand environment variables in the arguments

            cmd,*args = expanded #Split the command and arguments

            if cmd in BULITINS :
                BULITINS[cmd](*args) #Execute the built-in command
            else :
                try:
                    # If command contains '/', execute directly (quoted paths work here)
                    if "/" in cmd:
                        if not os.path.exists(cmd):
                            print(f"{cmd}: No such file or directory")
                        elif not os.access(cmd, os.X_OK):
                            print(f"{cmd}: Permission denied")
                        else:
                            subprocess.run([cmd] + args)
                    else:
                        # No slash → search PATH
                        subprocess.run([cmd] + args)

                except FileNotFoundError:
                    print(f"{cmd}: command not found")
                finally :
                    if stdin:
                        stdin.close()
        except EOFError:
            print() #Print a new line on EOF
            break
        

if __name__ == "__main__":
    main()
