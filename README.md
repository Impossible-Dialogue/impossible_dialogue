# Funkadelephant Lights
This project develops a new light system for the Funkadelephant art car. 

Design doc:
https://docs.google.com/document/d/193zCBdZJQ2zM1hZOcOoi2PbTF1X6veQUsoNvbH2qYzI/edit#heading=h.bk4r5cyiqgef

Photos of Funkadelephant BEFORE the lights upgrades:
https://photos.app.goo.gl/gXQorENS9bhVreZ16

3D Mesh files for the Funkadelephant art car:
https://drive.google.com/drive/folders/1XdZmZc8DAyeh26kRkMO6nCtN7fgZzTzO?usp=sharing

## attiny85 board
Each LED segment is controlled by a small attiny85 based board. The software for the board is in [attiny/attiny.ino](attiny/attiny.ino) file.

For the board to function correctly, we need to set fuses with the correct values to set the clock to 16Mhz internal and to enable Brown-out detection. There is a way to set the correct clock with the Arduino IDE, but it doesn’t enable the brown out detector. We also program the UID into the EEPROM and lock it using the EESAVE fuse to it persists when we update the application firmware. 
Here is the full list of fuse bits we need to set:

| Fuse          | Fuse Bit      | Notes                                                             |
| ------------- | ------------- | ----------------------------------------------------------------- |
| LOW           | CKSEL1        |                                                                   |
| LOW           | CKSEL2        |                                                                   |
| LOW           | CKSEL3        |                                                                   |
| HIGH          | SPIEN         |                                                                   |
| HIGH          | BODLEVEL2     | BODLEVEL 100 configure the brown out detector to 4.3V             | 
| HIGH          | EESAVE        | Lock EEPROM so it doesn’t get erased when programming             |
| EXTENDED      | SELFPRGEN     | Allow bootloader to program the flash                             |   

The board uses a simple bootloader that will enable us to update the main application over serial versus requiring a programmer attached to the chip. The bootloader is entered whenever the chip is powered on and it requires sending the CMD_BOOTLOADER message to enter the main application. The bootloader and also the main application communicate at 9600 baud by default. Before sending LED commands we typically want to increase the baudrate to a higher value, which is done using the CMD_SERIAL_BAUDRATE message. All of this is abstracted away in Python using the following initialization command:
``` 
serial_port = connection.InitializeController(tty_device, baudrate=250000)
``` 

### Program bootloader, set fuses, and UID
To get a board ready for use, we need to program the bootloader, set fuses, and burn the UID to EEPROM. All of this can be done using the [burn.sh](bootloader/burn.sh) script. With the USB programmer still attached burn the bootloader using the following commands:
``` 
cd bootloader
SEGMENT_UID=217
./burn.sh $SEGMENT_UID
``` 
After burning the bootloader will start immediately and display the UID on the LEDs. It will also output some debug information on pin 2.
If all looks good, disconnect the USB ISP programmer.

### Program main application 
The main application is in [attiny.ino](attiny/attiny.ino) and the compiled hex file is in [attiny.ino.tiny8.hex](attiny/attiny.ino.tiny8.hex). If the ino file is changed a new hex file can be generated using the Arduino IDU under `Sketch -> Export Compiled Binary`. This should overwrite [attiny.ino.tiny8.hex](attiny/attiny.ino.tiny8.hex).
NOTE: do NOT use the Arduino IDE or avrdude to program the main application. This will remove the bootloader.

To program the main application, connect to the (LED) serial and run:
``` 
cd controller
python flash_application.py
``` 
Note, flash_application will update the main application on all boards connected to the bus by default. Change the UID if only one boards should be updated.


## Visualization

The visualization consists of two parts right now. A server that serves LED control packets over websockets and a 3D visualizer written in javasript and three.js.

Note: the websockets server is currently not connected and reimplementing funky_lights.py. This should change. Either the two programs should become one or the websockets server should be able to listen to the serial coms created by funky_lights.py.

To start the websockets server:
``` 
cd visualization
python server.py
``` 

To start a webserver for the 3D visualizer run in the same folder:
``` 
python -m http.server
``` 

Now point a browser to http://localhost:8000/three.js/editor 

The LED configuration is loaded when opening the page. The Funky 3D object can be loaded optionally loaded (File->Import->funky.obj or File->Import->dome.obj). Also add some light sources (Add->Ambient/Directional lights).

The LED configuration was generated by fitting a 3D line to the mesh of one of the dome tubes, sampling 30 points along this line, and writing everything out in a simple JSON config format.

Run the following script to update the config:
``` 
python generate_led_config.py
``` 

Video of the prototype: https://youtu.be/v4KDhiCZiSY
