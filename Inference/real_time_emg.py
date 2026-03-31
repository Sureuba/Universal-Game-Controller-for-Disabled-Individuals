''' this connects the arduino to the emg buffer to the interference engine, to the game

arduino gets samples, emg buffer collects the sample, interference engine makes sense of it, game applies it
1. open arduino
2. create emgbuffer and interference engine
3. create connection to game via the socket, might change for future 
4. loop forever:
         - read one sample from arduni
         - add to buffer
          - if buffer ready:
            get latest sample 200
            predict gesture
            if high confidence
                send command to game

'''

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import serial #current talks to usb, will change to bluetooth?
import time
import socket
from collections import deque
from Inference.emg_buffer import EMGBuffer
import serial
from Inference.interference_engine import InterferenceEngine

# Majority voting: collect last VOTE_WINDOW predictions, only act if VOTE_THRESHOLD agree.
# Smooths out single-window misclassifications — the model rarely gets 3 in a row wrong.
VOTE_WINDOW = 5     # number of recent predictions to consider
VOTE_THRESHOLD = 5  # minimum agreeing votes needed to fire a command (unanimous)

def get_command(gesture):
    if gesture == 'clench':
        return 'jump'
    elif gesture == 'wrist':
        return 'duck'
    else:
        return 'run'



ARDUINO_PORT = 'COM3' #enter port
BAUD_RATE = 115200 # we are changing?

#prediction settings
CONFIDENCE_THRESHOLD = .85 #only act if model is 85% confident
COOLDOWN_TIME = 1.0 #wait 1.0 sec before sending same command

GAME_HOST = '127.0.0.1'  #??
GAME_PORT = 9999


def connect_to_game():
    "connecting via the tcp socket"
    print("connecting to da game")
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            client_socket.connect((GAME_HOST, GAME_PORT))
            print(f"connected to da game at{GAME_HOST}:{GAME_PORT}")
            return client_socket
        except ConnectionRefusedError:
            print("game not trying, hold up fr lol")
            time.sleep(1)

def run_real_time_classification():

    print("-" * 10)
    print("emg real time classification")
    print("-" * 10)


    print("opening up arduino connection")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE)
    ser.reset_input_buffer()
    time.sleep(2)
    print(f"we connected on the port {ARDUINO_PORT} ")

    print("init buffer and model")
    buffer = EMGBuffer(buffer_size=2000, window_size=200)
    engine = InterferenceEngine('student_model_best.pth', device='cpu') # or gpu if we have it
    print("b8ffer and model readyy")

    print("now connecting to game")
    game_socket = connect_to_game()

    #fill buffer

    print("now filling buffer")
    while not buffer.is_ready():
        line = ser.readline().decode('latin-1').strip()
        try:
            parts = line.split()
            value = int(parts[-1])  # last value is the muscle signal
            buffer.add_sample(value)
            if len(buffer.buffer) % 50 == 0:
                print(f"   {buffer.get_fill_percentage():.0f}%")
        except (ValueError, IndexError):
            continue

    print("buffer ready")
    print("now starting the real control")


    last_command_time = 0 #track when last sent a command
    last_gesture = None # track waht the last gesture was
    last_print = 0.0
    # vote_buffer stores the last VOTE_WINDOW gesture predictions.
    # a command only fires when VOTE_THRESHOLD or more of them agree,
    # filtering out single-window misclassifications.
    vote_buffer = deque(maxlen=VOTE_WINDOW)
    print(f"[EMG] Running — threshold: {CONFIDENCE_THRESHOLD:.0%}  cooldown: {COOLDOWN_TIME}s  voting: {VOTE_THRESHOLD}/{VOTE_WINDOW}")
    print("[EMG] Format:  GESTURE  confidence  status\n")
    try:  # Try-except for clean exit on Ctrl+C

        while True:  # Loop forever (until Ctrl+C)
            line = ser.readline().decode('latin-1').strip()  # Read one line from Arduino

            try:  # Try to convert to integer
                parts = line.split()
                value = int(parts[-1])  # last value is the muscle signal
            except (ValueError, IndexError):  # If line isn't a valid number
                continue  # Skip this iteration, go to next line

            buffer.add_sample(value)  # Add new sample to buffer (oldest drops off)
            window = buffer.get_latest_window()  # Get last 200 samples
            gesture, confidence = engine.predict(window)  # Predict gesture from window

            # Add prediction to vote buffer and find majority gesture
            vote_buffer.append(gesture)
            voted_gesture = max(set(vote_buffer), key=vote_buffer.count)
            vote_count = vote_buffer.count(voted_gesture)
            vote_passed = vote_count >= VOTE_THRESHOLD  # True if enough predictions agree

            current_time = time.time()  # Get current timestamp

            # Check if we should send command to game
            should_send = (  # Send if ALL conditions are true:
                vote_passed and                                          # majority vote agrees
                confidence >= CONFIDENCE_THRESHOLD and                   # model is confident enough (>70%)
                (current_time - last_command_time >= COOLDOWN_TIME or   # cooldown expired (0.5s passed)
                    voted_gesture != last_gesture)                       # OR it's a different gesture (immediate)
            )

            if should_send:  # If conditions met, send command
                command = get_command(voted_gesture)
                game_socket.sendall(command.encode())  # Send command to game as bytes
                print(f"[EMG] {voted_gesture.upper():<8} {confidence*100:.0f}%  → {command.upper()}")
                last_command_time = current_time  # Update last command time (for cooldown)
                last_gesture = voted_gesture  # Update last gesture (for change detection)

            # Print status once per second regardless of whether a command fired
            if current_time - last_print >= 1.0:
                if not vote_passed:
                    status = f"(voting: {vote_count}/{VOTE_THRESHOLD} needed)"
                elif confidence < CONFIDENCE_THRESHOLD:
                    status = f"(below {CONFIDENCE_THRESHOLD:.0%} threshold — no command)"
                elif not should_send:
                    status = "(cooldown active)"
                else:
                    status = "(sent)"
                print(f"[EMG] {voted_gesture.upper():<8} {confidence*100:.0f}%  {status}")
                last_print = current_time

    except KeyboardInterrupt: #so if the user presses control and c toegteher
        print("\n stopping rn") # tells us that we are stopping

    finally:   #always runs, even after exception, so we close arduino connnection
        ser.close() #closest arduino connection
        game_socket.close() #closes game connection
        print("closed")

if __name__ == '__main__': #if running file directly
    run_real_time_classification()


print(serial.VERSION)


