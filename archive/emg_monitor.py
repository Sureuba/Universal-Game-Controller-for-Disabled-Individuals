# emg_monitor.py - Displays incoming EMG gestures from dino_game.py
import socket
import datetime
os.chdir(os.path.dirname(os.path.abspath(__file__)))


PORT = 9998

RESET  = '\033[0m'
BOLD   = '\033[1m'
GREEN  = '\033[92m'
BLUE   = '\033[94m'
YELLOW = '\033[93m'
CYAN   = '\033[96m'
WHITE  = '\033[97m'
DIM    = '\033[2m'


GESTURE_STYLE = {
    'jump': (GREEN,  '  ^  ', ' / \\ ', '/   \\', ' JUMP '),
    'duck': (BLUE,   '_____', ' ___ ', '|   |', ' DUCK '),
    'run':  (YELLOW, '     ', ' >>> ', '     ', ' RUN  '),
}

def print_gesture(cmd):
    ts  = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]
    col, *art_lines, label = GESTURE_STYLE.get(cmd, (CYAN, '', '', '', cmd.upper()))
    bar = col + BOLD + '█' * 30 + RESET
    print(bar)
    for line in art_lines:
        print(f'  {col}{BOLD}{line}{RESET}')
    print(f'  {col}{BOLD}{label}{RESET}   {DIM}{ts}{RESET}')
    print(bar)
    print()

def main():
    print(f'\n{BOLD}{CYAN}╔══════════════════════════════╗')
    print(f'║     EMG GESTURE MONITOR      ║')
    print(f'║     listening on port {PORT}    ║')
    print(f'╚══════════════════════════════╝{RESET}\n')

    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(('127.0.0.1', PORT))
    srv.listen(1)
    print(f'{DIM}Waiting for game to connect...{RESET}\n')

    conn, addr = srv.accept()
    print(f'{GREEN}{BOLD}Game connected! Showing live EMG data:{RESET}')
    print(f'{DIM}{"─" * 32}{RESET}\n')

    while True:
        data = conn.recv(1024)
        if not data:
            break
        for cmd in data.decode().split():
            cmd = cmd.strip().lower()
            if cmd:
                print_gesture(cmd)

    print(f'\n{DIM}[Monitor] Connection closed.{RESET}')

if __name__ == '__main__':
    main()
