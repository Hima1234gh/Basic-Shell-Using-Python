import os
import sys
import shutil
import subprocess
import shlex
import re 
import readline
import glob


# Utility function to locate a command in the system PATH
# Finds the path in the given command

def get_path_commands():
    cmds = set()
    for path in os.environ.get("PATH", "").split(os.pathsep):
        if os.path.isdir(path):
            try:
                cmds.update(os.listdir(path))
            except PermissionError:
                pass
    return cmds

PATH_COMMANDS = get_path_commands()

def path_found(cmd) -> str:
    if path := shutil.which(cmd):
        return f"{cmd} is {path}" 
    else :
        return f"{cmd}: not found"

#expand environment variables in the given argument
def expand_vars(arg: str) -> str:
    def replace_var(match):
        var_name = match.group(1) or match.group(2)
        return os.environ.get(var_name, "") 
    pattern = r'\$(\w+)|\${(\w+)}'
    return re.sub(pattern, replace_var, arg)
    
def complete_commands(text):
    commands = set(BULITINS.keys())
    commands.update(PATH_COMMANDS)
    return sorted(cmd for cmd in commands if cmd.startswith(text))

def complete_paths(text):
    if not text:
        text = "."

    matches = glob.glob(text + "*")

    return sorted(
        m + "/" if os.path.isdir(m) else m
        for m in matches
    )


COMPLETERS = {
    "commands" : lambda text : complete_commands(text),
    "path" : lambda text : complete_paths(text),
}

# List of Built-in commands 
BULITINS = {
    "exit" : {"func": lambda code=0, *_ : sys.exit(int(code)), "complete" : None},
    "echo" : {"func": lambda *args : print(" ".join(args)), "complete" : None},
    "type" : {"func": lambda cmd=None, *_: print(f"{cmd} is a shell builtin") if cmd in BULITINS else print(path_found(cmd)), "complete" : None},
    "pwd" : {"func": lambda : print(subprocess.getoutput("pwd")), "complete" : None},
    "cd" : {"func": lambda path="~" : os.chdir(os.path.expanduser(path)) if os.path.exists(os.path.expanduser(path)) else print(f"cd: {path}: No such file or directory"), "complete" : None},
}

#redirection operators mapping
REDIRECTION_OPERATORS = {
    "<" : {"stream" : "stdin", "mode" : "r"},
    ">" : {"stream" : "stdout", "mode" : "w"},
    "1>" : {"stream" : "stdout", "mode" : "w"},
    ">>" : {"stream" : "stdout", "mode" : "a"},
    "1>>" : {"stream" : "stdout", "mode" : "a"},
    "2>" : {"stream" : "stderr", "mode" : "w"},
    "2>>" : {"stream" : "stderr", "mode" : "a"},
}

def append_space_if_needed(buffer, completion):
    if completion.endswith("/"):
        return completion            # directories → no space
    if buffer.endswith(" "):
        return completion            # already spaced
    return completion + " "


def completer(text, state):
    buffer = readline.get_line_buffer()

    try:
        tokens = shlex.split(buffer)
    except ValueError:
        tokens = buffer.split()

    if buffer.endswith(" ") or not tokens:
        curr_token = ""
        prev_token = tokens[-1] if tokens else ""
    else:
        curr_token = tokens[-1]
        prev_token = tokens[-2] if len(tokens) > 1 else ""

    if len(tokens) <= 1:
        options = COMPLETERS["commands"](curr_token)
    elif prev_token in REDIRECTION_OPERATORS:
        options = COMPLETERS["path"](curr_token)
    else:
        options = (
            COMPLETERS["commands"](curr_token) +
            COMPLETERS["path"](curr_token)
        )

    try:
        completion = options[state]
        return append_space_if_needed(buffer, completion)
        # if completion.endswith("/"):
        #     return completion
        # if buffer.endswith(" "):
        #     return completion
        # if len(options) > 1 :
        #     return  completion
        # return completion + " " 
    except IndexError:
        return None

    
#parse redirection from tokens
def parse_redirection(tokens):
    stdin = stdout = stderr = None
    i = 0

    while i < len(tokens) :
        tok = tokens[i] 

        if tok in REDIRECTION_OPERATORS :
            if i + 1 >= len(tokens) :
                print("syntax error near unexpected token")
                return None, None, None, None
            
            # get the file name for redirection
            file_name = tokens[i+1]
            stream = REDIRECTION_OPERATORS[tok]["stream"]
            mode = REDIRECTION_OPERATORS[tok]["mode"]

            try :
                f = open(file_name, mode)
            except FileNotFoundError :
                print(f"{file_name}: No such file or directory")
                return None, None, None, None       
            except PermissionError :
                print(f"{file_name}: Permission denied")
                return None, None, None, None       

            # assign the file object to the appropriate stream
            if stream == "stdin" :
                stdin = f 
            elif stream == "stdout" :
                stdout = f
            elif stream == "stderr" :
                stderr = f

            del tokens[i:i+2]
            continue

        i += 1
    return tokens,stdin, stdout, stderr    

def display_matches_hook(substitution, matches, longest_match_length):
    sys.stdout.write("\n")
    clean_matches = [m.strip() for m in matches]
    sys.stdout.write("  ".join(clean_matches))
    sys.stdout.write("\n")
    sys.stdout.flush()
    readline.redisplay()



readline.parse_and_bind("tab: complete")
readline.set_completer(completer)
readline.set_completer_delims(" \t\n;<>|&")
readline.set_completion_display_matches_hook(display_matches_hook)


# Main function to run the shell
def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()

            user_input = input()#user input

            try:
                tokens = shlex.split(user_input, posix=True)
            except ValueError as ve:
                print(f"Error parsing input: {ve}")
                continue

            if not user_input:
                continue

            #expand variables in tokens
            expanded = [expand_vars(arg) for arg in tokens]

            #parse redirection  
            parsed = parse_redirection(expanded)

            if parsed[0] is None:
                continue

            tokens, stdin, stdout, stderr = parsed #unpack parsed values

            cmd, *args = tokens #command and arguments

            
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

                    BULITINS[cmd]["func"](*args)

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
