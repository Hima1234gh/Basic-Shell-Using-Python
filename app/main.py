import os
import sys
import shutil
import subprocess
import shlex
import re
import readline
import glob

#utilities 
readline.set_auto_history(False)
HISTOTY_FILE = os.path.expanduser("~/.pyshell_history")

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

def _history_impl(*args):
    length = readline.get_current_history_length()

    if args and args[0] == "-c":
        readline.clear_history()
        open(HISTOTY_FILE, 'w').close()
        return
    
    if args and args[0] == "-r" :
        filname = args[1] if len(args) > 1 else HISTOTY_FILE
        try :
            readline.read_history_file(filname) 
        except FileNotFoundError :
            pass
        return   
    
    if args and args[0] == "-w" :
        filname = args[1] if len(args) > 1 else HISTOTY_FILE
        try :
            readline.write_history_file(filname) 
        except FileNotFoundError :
            pass
        return

    if args and args[0].isdigit():
        n = int(args[0])
        start = max(1, length - n + 1)
    else:
        start = 1

    for i in range(start, length + 1):
        item = readline.get_history_item(i)
        if item:
            print(f"{i:5d}  {item}")

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
    "history": {"func": lambda *args: _history_impl(*args),}
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

def execute_pipeline(commands):
    processes = []
    prev_read = None  # read end of previous pipe

    for i, cmd in enumerate(commands):
        cmd = [expand_vars(arg) for arg in cmd]
        is_builtin = cmd[0] in BUILTINS

        # create pipe unless last command
        if i < len(commands) - 1:
            read_fd, write_fd = os.pipe()
            stdout_fd = write_fd
        else:
            read_fd = write_fd = None
            stdout_fd = None

        stdin_fd = prev_read

        if is_builtin:
            pid = os.fork()

            if pid == 0:
                # CHILD
                if stdin_fd is not None:
                    os.dup2(stdin_fd, 0)
                if stdout_fd is not None:
                    os.dup2(stdout_fd, 1)

                # close all pipe fds in child
                if stdin_fd is not None:
                    os.close(stdin_fd)
                if stdout_fd is not None:
                    os.close(stdout_fd)
                if read_fd is not None:
                    os.close(read_fd)

                BUILTINS[cmd[0]]["func"](*cmd[1:])
                os._exit(0)

            else:
                # PARENT
                processes.append(pid)

        else:
            try:
                p = subprocess.Popen(
                    cmd,
                    stdin=stdin_fd,
                    stdout=stdout_fd
                )
                processes.append(p)
            except FileNotFoundError:
                print(f"{cmd[0]}: command not found")
                return

        # parent closes used fds
        if stdin_fd is not None:
            os.close(stdin_fd)
        if stdout_fd is not None:
            os.close(stdout_fd)

        prev_read = read_fd

    # close final read end
    if prev_read is not None:
        os.close(prev_read)

    # wait for all children
    for p in processes:
        if isinstance(p, int):
            os.waitpid(p, 0)
        else:
            p.wait()


def load_history():    
    readline.clear_history()

def save_history():
    readline.write_history_file(HISTOTY_FILE)

#main loop
def main():
    load_history()
    try :
        while True:
            
            try:
                user_input = input("$ ")

                if user_input.strip() : #and user_input.startswith("history -r"):
                    readline.add_history(user_input)
                if not user_input:
                    continue

                commands = parse_input(user_input)

                if len(commands) == 1:
                    execute_single_command(commands[0])
                else:
                    execute_pipeline(commands)

            except EOFError:
                print()
                break
    except EOFError :
        print()
    except KeyboardInterrupt :
        print()
    finally:
        save_history()

if __name__ == "__main__":
    main()