import os
import random
from pathlib import Path
from rembg import remove
from PIL import Image
from cv2 import VideoCapture, imshow, imwrite, waitKey, destroyWindow
from send_mail import send_mail
import datetime
import onnxruntime

BASE = Path("tex/main.tex")
AURAFARBEN = ["Gelb", "Gold", "Schwarz", "Rosa", "Grün", "Blau", "Rot"]


def compile_doc(name, color_one, color_two, send=False):
    latex_document = './tex/vars.tex'

    latex_code = f"""\ErstelleAuraDokument{{{name}}}{{\\today}}{{{color_one}}}{{{color_two}}}"""
    with open(latex_document, 'w') as file:
        file.write(latex_code)

    cur_timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    command = f"pdflatex -output-directory=../Measurements -jobname={cur_timestamp}-{name} main.tex"
    os.system(f"cd tex && {command}")
    unnecessary_file_extensions = [".log", ".out", ".toc"]
    for extension in unnecessary_file_extensions:
        os.system(f"cd Measurements && pwd && mv *{extension} ./aux")
    return f"{cur_timestamp}-{name}.pdf"


def capture_image():

    # Initialize webcam (0 = default camera)
    cam = VideoCapture(0)

    # Capture one frame
    ret, frame = cam.read()

    if ret:
        #imshow("Captured", frame)
        imwrite("captured_image.png", frame)
        #waitKey(0)
        #destroyWindow("Captured")
    else:
        print("Failed to capture image.")

    cam.release()

def remove_background(input_file_path, output_file_path):
    # Processing the image
    input = Image.open(input_file_path)

    # Removing the background from the given Image
    output = remove(input)

    #Saving the image in the given path
    output.save(output_file_path)

def get_random_aura_color():
    aura_color_one = random.choice(AURAFARBEN)
    aura_color_two = random.choice(AURAFARBEN)
    while aura_color_one == aura_color_two:
        aura_color_two = random.choice(AURAFARBEN)
    return aura_color_one, aura_color_two

def cleanup_fs():
    # delete all pdfs and face.png
    if os.path.isfile("tex/face.png"):
        os.remove("tex/face.png")
    if os.path.isfile("captured_image.png"):
        os.remove("captured_image.png")

if __name__ == "__main__":
    cleanup_fs()
    capture_image()
    remove_background("captured_image.png", "tex/face.png")
    aura_colors = get_random_aura_color()
    compile_doc("Jonah", aura_colors[0], aura_colors[1])
    try:
        send_mail("conference@borjs.de", "Deine Auramessung", "Hallo! Im Anhang kannst du deine Auramessung einsehen! Viel Spaß mit diesen Wissenschaftlich fundierten Daten!", files=["../Auramessung.pdf"])
    except:
        print ("Sending the mail went wrong :c")
    cleanup_fs() # second remove after script ran