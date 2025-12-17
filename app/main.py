import sys


def main():
    sys.stdout.write("$ ")
    command = input()
    while command != " ":
        sys.stdout.write(f"Executing command: {command}\n")
        sys.stdout.write("$ ")
        command = input()



if __name__ == "__main__":
    main()
