import Tkinter as tk
import cv2
import numpy as np
import tkMessageBox, tkFileDialog
from PIL import Image, ImageTk
from scanner import Scanner
from renderer import RenderParams, Renderer
from math import hypot

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def vertical_separator(parent, width):
    return tk.Frame(parent, height=3, width=width, bd=1, relief=tk.SUNKEN)

def horizontal_separator(parent, height):
    return tk.Frame(parent, height=height, width=3, bd=1, relief=tk.SUNKEN)

class ButtonBar(tk.Frame):
    def __init__(self, parent, app, width, height, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.app = app
        self.build_scanner_input_menus(width, height)
        self.build_action_buttons(width, height)

    def refresh_scanner_input_menus(self):
        self.arduino_menu.option_clear()
        for option in Scanner.list_arduinos_candidates():
            self.arduino_menu.option_add(option, option)
        self.camera_menu.option_clear()
        for option in Scanner.list_cameras_indexes():
            self.camera_menu.option_add(str(option), str(option))

    def build_scanner_input_menus(self, w, h):
        tk.Button(self, text="Detect", command=self.refresh_scanner_input_menus).pack()

        tk.Label(self, text="Arduino serial port").pack()
        self.arduino = tk.StringVar(self)
        self.arduino.set(self.app.scanner.arduino_dev)
        options = Scanner.list_arduinos_candidates()
        self.arduino_menu = tk.OptionMenu(self, self.arduino, *options)
        self.arduino_menu.pack()
        
        tk.Label(self, text="Camera number").pack()
        self.camera = tk.StringVar(self)
        self.camera.set(str(self.app.scanner.cam_id))
        options = Scanner.list_cameras_indexes()
        self.camera_menu = tk.OptionMenu(self, self.camera, *options)
        self.camera_menu.pack()
        
        vertical_separator(self, w).pack()

    def build_action_buttons(self, w, h):
        tk.Button(self, text="Scan", command=self.app.scan).pack()
        tk.Button(self, text="Open dump", command=self.app.open).pack()
        vertical_separator(self, w).pack()

class ImageZone(tk.Frame):
    def __init__(self, parent, app, width, height, **kwargs):
        tk.Frame.__init__(self, parent, width=width, height=height, **kwargs)
        self.app = app
        self.W, self.H = width, height
        self.imglabel = tk.Label(self)
        self.show_image(0x33*np.ones((height, width, 3), dtype=np.uint8))
        self.imglabel.pack()
        self.imglabel.bind('<Button-1>', self.clicked)

    def clicked(self, event):
        self.app.Cx.set(float(event.x)/self.W)
        self.app.Cy.set(float(event.y)/self.H)
        self.show_cross()
        self.app.calibrated.set(True)

    def show_image(self, image):
        if tuple(image.shape[:2]) != (self.H, self.W):
            image = cv2.resize(image, (self.W, self.H), interpolation=cv2.INTER_AREA)
        self.image = image
        self.imgtk = ImageTk.PhotoImage(image=Image.fromarray(self.image))
        self.imglabel.configure(image=self.imgtk)

    def show_cross(self):
        self.overlay = np.zeros(self.image.shape)
        x = self.W * self.app.Cx.get()
        y = self.H * self.app.Cy.get()
        for i in range(self.W):
            self.overlay[y][i] = np.array([255, -255, -255])
        for i in range(self.H):
            self.overlay[i][x] = np.array([255, -255, -255])
        layers = np.array((self.image + self.overlay).clip(0, 255), dtype=np.uint8)
        self.imgtk = ImageTk.PhotoImage(image=Image.fromarray(layers))
        self.imglabel.configure(image=self.imgtk)

    def show_3D(self, points):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d', aspect="equal")
        X, Y, Z = zip(*points)
        ax.scatter(X, Y, Z, alpha=0.25)
        R = 250
        disk = [(x, y, 0) for x in np.linspace(-R, R) for y in np.linspace(-R, R) if hypot(x, y) <= R]
        diskX, diskY, diskZ = zip(*disk)
        ax.plot(diskX, diskY, diskZ, '.', color='g', alpha=0.25)
        ax.set_xlim(-R, R)
        ax.set_ylim(-R, R)
        ax.set_zlim(-R, R)
        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


class InfoBar(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        tk.Label(self, text="Semiteleporter, the 3D Scanner. Quit with ctrl-q or ctrl-w").pack()

class MainFrame(tk.Frame):
    def __init__(self, app, **kwargs):
        iH = 500 # Image height
        iW = int(iH*app.scanner.aspect()) # Image width
        bW, bH = 200, 100 # Bars width and height
        W, H = iW + bW, iH + bH
        tk.Frame.__init__(self, app, width=W, height=H, **kwargs)
        self.pack(fill=tk.BOTH)
        self.infobar = InfoBar(self, app, width=W, height=bH)
        self.infobar.pack()
        self.imgzone = ImageZone(self, app, width=iW, height=iH)
        self.imgzone.pack(side="left")
        self.butbar = ButtonBar(self, app, width=bW, height=iH)
        self.butbar.pack(side="right")

class App(tk.Tk):
    def __init__(self, scanner):
        tk.Tk.__init__(self)
        self.scanner = scanner
        self.bind('<Control-q>', lambda ev: self.quit())
        self.bind('<Control-w>', lambda ev: self.quit())

        # Configuration variables
        self.arduino = tk.StringVar(self)
        self.arduino.set(scanner.arduino_dev)
        self.camera = tk.StringVar(self)
        self.camera.set(str(scanner.cam_id))
        self.frame = MainFrame(self)
        
        # Calibration
        self.Cx = tk.DoubleVar(self)
        self.Cx.set(0.5)
        self.Cy = tk.DoubleVar(self)
        self.Cy.set(0.5)
        self.calibrated = tk.BooleanVar(self)
        self.calibrated.set(False)

    def do_scan(self):
        params = RenderParams(
            CX=self.Cx.get()*self.scanner.W,
            CY=self.Cy.get()*self.scanner.H
        )
        all_points = []
        for points in Renderer(params, self.scan_iter):
            print points
            all_points += points[0]
        self.frame.imgzone.show_3D(all_points)

    def scan(self):
        if self.calibrated.get():
            self.do_scan()
        else:
            tkMessageBox.showinfo(
                "Calibration", 
                "The scanner is not calibrated yet. It will now take a sample "+
                "picture to determine initial lasers position. The image will "+
                "be displayed in the window. Please click on the image, in "+
                "order to align the red cross with the center of the yellow "+
                "cross, then click on \"Scan\" again."
            )
            self.scanner.arduino_dev = self.arduino.get()
            self.scanner.cam_id = int(self.camera.get())
            mask = self.scanner.calibrate()
            self.frame.imgzone.show_image((255*mask))
            self.scan_iter = self.scanner.scan()
            

    def open(self):
        self.calibrated.set(False)
        from_dir = tkFileDialog.askdirectory(mustexist=True)
        mask = self.scanner.calibrate_from(from_dir)
        if mask is None:
            tkMessageBox.showerror("File error", "Unable to open dump dir")
        else:
            self.frame.imgzone.show_image((255*mask))
            tkMessageBox.showinfo(
                "Calibration", 
                "The image set is not calibrated yet. Please click on the image in "+
                "order to align the red cross on the center of the yellow cross. "+
                "Then, click on \"Scan\" to continue."
            )
            self.scan_iter = self.scanner.replay(from_dir)

if __name__ == "__main__":
    gui = App(Scanner())
    gui.mainloop()
    gui.destroy()
