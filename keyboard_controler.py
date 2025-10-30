from pynput import keyboard

def check_arrows():
    def on_press(key):
        
        if key == keyboard.Key.up:
            print("Up arrow pressed")
        elif key == keyboard.Key.down:
            print("Down arrow pressed")
        elif key == keyboard.Key.left:
            print("Left arrow pressed")
        elif key == keyboard.Key.right:
            print("Right arrow pressed")
        elif key == keyboard.Key.ctrl_r:
            raise('Fuck')
        

    # Create a listener that runs until you stop it with Ctrl+C
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

if __name__ == "__main__":
    check_arrows()
