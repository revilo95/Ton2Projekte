
#import PP2
import tkinter as tk
from tkinter import filedialog


def load_file():
    file_path = filedialog.askopenfilename()
    if file_path:
        print("File loaded:", file_path)  # Replace with your file handling code

def update_slider_value(slider, label):
    value = slider.get()
    label.config(text=f"Value: {value}")

def start_play(slider):
    print(f"Playing slider {slider}")

root = tk.Tk()
root.title("Sliders and File Load")
root.geometry("200x400")

# Function to handle slider value changes
def on_slider_change(*args):
    update_slider_value(slider1, label1)
    update_slider_value(slider2, label2)
    update_slider_value(slider3, label3)

# Load File Button
load_button = tk.Button(root, text="Load File", command=load_file)
load_button.pack()

# Slider 1
label1 = tk.Label(root, text="Lineares Panning: 0")
label1.pack()
slider1 = tk.Scale(root, from_=0, to=180, orient="horizontal", command=on_slider_change)
slider1.set(90)
slider1.pack()

# Play Button for Slider 1
play_button1 = tk.Button(root, text="Play", command=lambda: start_play(1))
play_button1.pack()

# Slider 2
label2 = tk.Label(root, text="Value: 0")
label2.pack()
slider2 = tk.Scale(root, from_=0, to=100, orient="horizontal", command=on_slider_change)
slider2.set(50)
slider2.pack()

# Play Button for Slider 2
play_button2 = tk.Button(root, text="Play", command=lambda: start_play(2))
play_button2.pack()

# Slider 3
label3 = tk.Label(root, text="Value: 0")
label3.pack()
slider3 = tk.Scale(root, from_=0, to=100, orient="horizontal", command=on_slider_change)
slider3.set(50)
slider3.pack()

# Play Button for Slider 3
play_button3 = tk.Button(root, text="Play", command=lambda: start_play(3))
play_button3.pack()



root.mainloop()

