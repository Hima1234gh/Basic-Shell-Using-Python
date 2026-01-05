import os
import sys
import shutil
import subprocess
import shlex
import re
import readline
import glob

#utilities 

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

#check if command exists in PATH
def path_found(cmd: str) -> str:
    path = shutil.which(cmd)
    return f"{cmd} is {path}" if path else f"{cmd}: not found"

#expand environment variables in arguments
def expand_vars(arg: str) -> str:
    pattern = r'\$(\w+)|\${(\w+)}'

    def replace(match):
        name = match.group(1) or match.group(2)
        return os.environ.get(name, "")

    return re.sub(pattern, replace, arg)

#Buitlin commands

BUILTINS = {
    "exit": {"func": lambda code=0, *_: sys.exit(int(code))},
    "echo": {"func": lambda *args: print(" ".join(args))},
    "type": {"func": lambda cmd=None, *_:
             print(f"{cmd} is a shell builtin") if cmd in BUILTINS else print(path_found(cmd))},
    "pwd": {"func": lambda: print(subprocess.getoutput("pwd"))},
    "cd": {"func": lambda path="~":
           os.chdir(os.path.expanduser(path))
           if os.path.exists(os.path.expanduser(path))
           else print(f"cd: {path}: No such file or directory")},
}

#Redirection parsing
REDIRECTION_OPERATORS = {
    "<":  ("stdin", "r"),
    ">":  ("stdout", "w"),
    "1>": ("stdout", "w"),
    ">>": ("stdout", "a"),
    "1>>":("stdout", "a"),
    "2>": ("stderr", "w"),
    "2>>":("stderr", "a"),
}

#parse redirection operators in command tokens
def parse_redirection(tokens):
    stdin = stdout = stderr = None
    i = 0

    while i < len(tokens):
        tok = tokens[i]

        if tok in REDIRECTION_OPERATORS:
            if i + 1 >= len(tokens):
                print("syntax error near unexpected token")
                return None, None, None, None

            stream, mode = REDIRECTION_OPERATORS[tok]
            filename = tokens[i + 1]

            try:
                f = open(filename, mode)
            except Exception as e:
                print(e)
                return None, None, None, None

            if stream == "stdin":
                stdin = f
            elif stream == "stdout":
                stdout = f
            else:
                stderr = f

            del tokens[i:i + 2]
            continue

        i += 1

    return tokens, stdin, stdout, stderr

#parse user input into commands and arguments
def parse_input(user_input: str):
    try:
        tokens = shlex.split(user_input, posix=True)
    except ValueError as e:
        print(f"Error parsing input: {e}")
        return []

    commands, current = [], []

    for tok in tokens:
        if tok in ("|", "&", ";"):
            commands.append(current)
            current = []
        else:
            current.append(tok)

    if current:
        commands.append(current)

    return commands

#tab completion functions
def complete_commands(text):
    cmds = set(BUILTINS.keys())
    cmds.update(PATH_COMMANDS)
    return sorted(c for c in cmds if c.startswith(text))

#complete filesystem paths
def complete_paths(text):
    text = text or "."
    matches = glob.glob(text + "*")
    return sorted(m + "/" if os.path.isdir(m) else m for m in matches)

#tab completer function
def completer(text, state):
    buffer = readline.get_line_buffer()

    try:
        tokens = shlex.split(buffer)
    except ValueError:
        tokens = buffer.split()

    curr = tokens[-1] if tokens and not buffer.endswith(" ") else ""

    options = complete_commands(curr) + complete_paths(curr)

    try:
        return options[state] + (" " if not options[state].endswith("/") else "")
    except IndexError:
        return None

#display matches hook for tab completion
def display_matches_hook(substitution, matches, longest):
    buffer = readline.get_line_buffer()
    sys.stdout.write("\n")
    sys.stdout.write("  ".join(m.strip() for m in matches))
    sys.stdout.write("\n$ " + buffer)
    sys.stdout.flush()

#setup readline for tab completion
readline.parse_and_bind("tab: complete")
readline.set_completer(completer)
readline.set_completer_delims(" \t\n;<>|&")
readline.set_completion_display_matches_hook(display_matches_hook)

#execute a single command with possible redirections
def execute_single_command(command):
    expanded = [expand_vars(arg) for arg in command]
    parsed = parse_redirection(expanded)

    if parsed[0] is None:
        return

    tokens, stdin, stdout, stderr = parsed
    cmd, *args = tokens

    if cmd in BUILTINS:
        saved = sys.stdin, sys.stdout, sys.stderr
        if stdin: sys.stdin = stdin
        if stdout: sys.stdout = stdout
        if stderr: sys.stderr = stderr

        try:
            BUILTINS[cmd]["func"](*args)
        finally:
            sys.stdin, sys.stdout, sys.stderr = saved
    else:
        try:
            subprocess.run([cmd] + args, stdin=stdin, stdout=stdout, stderr=stderr)
        except FileNotFoundError:
            print(f"{cmd}: command not found")

    for f in (stdin, stdout, stderr):
        if f:
            f.close()

def execute_pipline_command(command):
    process = []
    prev_read = None

    for i, cmd in enumerate(command) :
        cmd = [expand_vars(arg) for arg in cmd]

        if i < len(command) - 1:
            read_fd, write_fd = os.pipe()
            stdout = write_fd
        else :
            read_fd = write_fd = None
            stdout = None

        stdin = prev_read

        try :
            p = subprocess.Popen(cmd, stdin=stdin, stdout=stdout)
            process.append(p)
        except FileNotFoundError:
            print(f"{cmd[0]}: command not found")
            for pr in process:
                pr.terminate()
            return
        
        if stdin is not None:
            os.close(stdin)
        if stdout is not None:
            os.close(stdout)      
        prev_read = read_fd

        for p in process :
            p.wait()

#main loop
def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()

            user_input = input()
            if not user_input:
                continue

            commands = parse_input(user_input)

            if len(commands) == 1:
                execute_single_command(commands[0])
            else:
                execute_pipline_command(commands)   

        except EOFError:
            print()
            break

if __name__ == "__main__":
    main()
