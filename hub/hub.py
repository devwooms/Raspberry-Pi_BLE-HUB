import os
import sys
import argparse
from ui.terminal_menu import TerminalMenu

def main():
    """메인 함수"""
    menu = TerminalMenu()
    menu.main_menu()

if __name__ == "__main__":
    main() 