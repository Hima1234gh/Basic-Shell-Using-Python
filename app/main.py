import sys


def main():
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
            if commands[0] == "echo":
                print(" ".join(commands[1:]))
            else:
                sys.stdout.write(f"{commands[0]}: command not found\n")
        

if __name__ == "__main__":
    main()
