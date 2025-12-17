import sys


def main():
    sys.stdout.write("$ ")
    command = input()
    while command != "exit":
        sys.stdout.write("$ ")
        command = input()
        commands = command.split()
        if command[0] == "echo" :
            print(" ".join(commands[1:]))
        else :
            print(f"{command}: command not found")
        



if __name__ == "__main__":
    main()
