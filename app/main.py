import os
import sys
import shutil
import subprocess
import shlex
import re 

# Utility function to locate a command in the system PATH
# Finds the path in the given command
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


# List of Built-in commands 
BULITINS = {
    "exit" : lambda code=0, *_ : sys.exit(int(code)),
    "echo" : lambda *args : print(" ".join(args)),
    "type" : lambda cmd=None, *_: print(f"{cmd} is a shell builtin") if cmd in BULITINS else print(path_found(cmd)),
    "pwd" : lambda : print(subprocess.getoutput("pwd")),
    "cd" : lambda path="~" : os.chdir(os.path.expanduser(path)) if os.path.exists(os.path.expanduser(path)) else print(f"cd: {path}: No such file or directory"),
}


# Main function to run the shell
def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()

            user_input = input()

            stdin = None
            stdout = None
            stderr = None

            try:
                tokens = shlex.split(user_input, posix=True)
            except ValueError as ve:
                print(f"Error parsing input: {ve}")
                continue

            if not user_input:
                continue

            
            if "<" in tokens:
                idx = tokens.index("<")

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

                del tokens[idx:idx + 2]

            
            i = 0
            while i < len(tokens):
                tok = tokens[i]

                if tok in (">", "1>"):
                    if i + 1 >= len(tokens):
                        print("syntax error near '>'")
                        break
                    outfile = tokens[i + 1]
                    stdout = open(outfile, "w")
                    del tokens[i:i+2]
                    continue

                if tok == ">>":
                    if i + 1 >= len(tokens):
                        print("syntax error near '>>'")
                        break
                    outfile = tokens[i + 1]
                    stdout = open(outfile, "a")
                    del tokens[i:i+2]
                    continue

                if tok == "2>":
                    if i + 1 >= len(tokens):
                        print("syntax error near '2>'")
                        break
                    errfile = tokens[i + 1]
                    stderr = open(errfile, "w")
                    del tokens[i:i+2]
                    continue

                i += 1

            
            expanded = [expand_vars(arg) for arg in tokens]

            cmd, *args = expanded

            
            if cmd in BULITINS:
                # Builtins also respect redirection
                saved_stdin = sys.stdin
                saved_stdout = sys.stdout
                saved_stderr = sys.stderr

                try:
                    if stdin:
                        sys.stdin = stdin
                    if stdout:
                        sys.stdout = stdout
                    if stderr:
                        sys.stderr = stderr

                    BULITINS[cmd](*args)

                finally:
                    sys.stdin = saved_stdin
                    sys.stdout = saved_stdout
                    sys.stderr = saved_stderr

            else:
                try:
                    if "/" in cmd:
                        if not os.path.exists(cmd):
                            print(f"{cmd}: No such file or directory")
                        elif not os.access(cmd, os.X_OK):
                            print(f"{cmd}: Permission denied")
                        else:
                            subprocess.run(
                                [cmd] + args,
                                stdin=stdin,
                                stdout=stdout,
                                stderr=stderr
                            )
                    else:
                        subprocess.run(
                            [cmd] + args,
                            stdin=stdin,
                            stdout=stdout,
                            stderr=stderr
                        )

                except FileNotFoundError:
                    print(f"{cmd}: command not found")

            
            if stdin:
                stdin.close()
            if stdout:
                stdout.close()
            if stderr:
                stderr.close()

        except EOFError:
            print()
            break


if __name__ == "__main__":
    main()
