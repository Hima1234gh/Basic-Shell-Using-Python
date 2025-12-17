import sys


def main():
    system_command = ["echo", "exit", "type"]
    while True:
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
            if commands[0] in system_command:
                if commands[0] == "\n":
                    sys.stdout.write(f"{commands[0]} is a shell bultin\n")
                elif commands[0] == "echo":
                    sys.stdout.write(" ".join(commands[1:]) + "\n")
            else:
                sys.stdout.write(f"{commands[0]}: command not found\n")
        

if __name__ == "__main__":
    main()
