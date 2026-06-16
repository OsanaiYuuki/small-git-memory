import sys
sys.stdout.reconfigure(encoding="utf-8")

from core.git_memory import GitMemory
from cli import run_cli

def main():
    memory=GitMemory()
    run_cli(memory)

if __name__ == "__main__":
    main()