# PyShell 🐚  
*A Bash-like Unix shell implemented in Python*

PyShell is a lightweight Unix-style shell written in Python that mimics core Bash behavior.  
It supports built-in commands, pipelines, redirection, environment variable expansion, command history with persistence, and tab completion using GNU Readline.

This project was built as a **systems-level learning exercise**, inspired by the Codecrafters Shell Challenge.

---

## ✨ Features

### 🧠 Shell Core
- Command parsing with `shlex`
- Execution of external commands via `subprocess`
- Built-in command support
- Environment variable expansion (`$VAR`, `${VAR}`)

### 🔗 Pipelines & Redirection
- Pipes (`|`)
- Input redirection (`<`)
- Output redirection (`>`, `>>`)
- File descriptor redirection (`1>`, `2>`)

### 📜 History Management (Bash-like)
- Persistent command history across sessions
- `HISTFILE` environment variable support
- Built-in `history` command with:
  - `history` – show history
  - `history -a [file]` – append new commands
  - `history -r [file]` – read history from file
  - `history -w [file]` – write history to file
  - `history -c` – clear in-memory history
- Correct incremental append behavior (no duplicates)

### ⌨️ User Experience
- Tab completion for:
  - Built-in commands
  - Executables in `$PATH`
  - Files and directories
- Command auto-completion display
- Interactive prompt (`$ `)

---

## 🛠 Built-in Commands

| Command  | Description |
|--------|------------|
| `cd` | Change directory |
| `pwd` | Print current directory |
| `echo` | Print arguments |
| `type` | Identify command type |
| `history` | Manage command history |
| `exit` | Exit the shell |



---

## 🚀 How to Run

### Requirements
- Linux (tested on Ubuntu)
- Python 3.8+
- GNU Readline

### Run the shell
```bash
python3 main.py
