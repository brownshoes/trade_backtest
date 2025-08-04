def demo_ansi_colors():
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"

    print(f"{BOLD}ANSI Color and Style Demo{RESET}\n")

    print(f"{RED}This is red text{RESET}")
    print(f"{GREEN}This is green text{RESET}")
    print(f"{YELLOW}This is yellow text{RESET}")
    print(f"{BLUE}This is blue text{RESET}")
    print(f"{MAGENTA}This is magenta text{RESET}")
    print(f"{CYAN}This is cyan text{RESET}")

    print()

    print(f"{BOLD}This text is bold{RESET}")
    print(f"{UNDERLINE}This text is underlined{RESET}")

    print()

    print(f"{RED}{BOLD}Bold red text{RESET}")
    print(f"{GREEN}{UNDERLINE}Underlined green text{RESET}")

if __name__ == "__main__":
    demo_ansi_colors()
