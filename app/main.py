import sys


def main():
    sys.stdout.write("$ ")
    command = input()
    while command != "exit":
        sys.stdout.write(f"{command}: command not found\n")
        sys.stdout.write("$ ")
        command = input()



if __name__ == "__main__":
    main()
