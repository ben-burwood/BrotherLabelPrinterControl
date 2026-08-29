### Labelprinterkit

Labelprinterkit is a Python3 library for creating and printing labels with
Brother P-Touch devices. It was developed for the Networking department of
KIT (Karlsruhe Institute of Technology).

Labelprinterkit's simple layout engine can be used to create simple labels:

```python
from labelprinterkit.backends.usb import PyUSBBackend
from labelprinterkit.printers import P700
from labelprinterkit.label import Label, Padding
from labelprinterkit.labels.box import Box
from labelprinterkit.labels.text import Text
from labelprinterkit.job import Job
from labelprinterkit.constants import Media
from labelprinterkit.page import Page
from PIL import Image

# Create text for the label

text1 = Text(45, "First line", "comic.ttf", padding=Padding(0, 0, 1, 0))
text2 = Text(25, "Some text", "comic.ttf")
text3 = Text(25, "Other text", "comic.ttf")

# Insert Text into boxes
box1 = Box(45, text1)
box2 = Box(25, text2, text3)

# Create label with rows from above
label = Label(box1, box2)

# Create job with configuration and add label as page
job = Job(Media.W12)
job.add_page(label)

# Create a page from a Pillow image and add it to the job
image = Image.new("1", (70, 200), "white")
page = Page.from_image(image)
job.add_page(page)

# scan for a USB printer using the PyUSBBackend
backend = PyUSBBackend()
printer = P700(backend)

# Print job
printer.print(job)
```

To use a Bluetooth connection:

1. pair your device
2. specify the serial device node when instantiating the printer:

```python
printer = GenericPrinter(BTSerialBackend(dev_path="/dev/ttyS8"))
```

The following printers are currently supported:

* Brother P-Touch PT-700 (aka P700)
* Brother P-Touch PT-750W (aka P750W)
* Brother H500
* Brother E500

The following printers have been tested to mostly work, although not
officially supported (their protocol is similar, although not identical):

* Brother P-touch CUBE Plus PTP710BT

The following backends are currently supported:

* USB Printer Device Class via PyUSB
* Bluetooth Serial connection via PySerial
* Network connection via TCP

The official source of this repository is at https://git.scc.kit.edu/scc-net/labelprinterkit.
Pull requests and issues are also accepted on github at https://github.com/ogelpre/labelprinterkit.
