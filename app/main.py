import sys


def main():
    while True:
            comm = ["type", "echo", "exit"]
            try:
                sys.stdout.write("$ ")
                sys.stdout.flush()
                command = input()
            except EOFError:
                break

            if command.strip() == "exit":
                break

            if not command.strip():
                continue

            commands = command.split()
            
            if commands[0] == "echo":
                sys.stdout.write(" ".join(commands[1:]) + "\n")
            elif commands[0] == "type" and commands[1] in comm:
                sys.stdout.write(f"{commands[1]} is a shell builtin\n")
            else:
                sys.stdout.write(f"{commands[0]}: command not found\n")
        

if __name__ == "__main__":
    main()
