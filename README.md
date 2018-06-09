# mitemp_bt - Library for Xiaomi Mi Temperature and Humidity Sensor (v2) with Bleutooth LE and the LCD display


This library lets you read sensor data from a Xiaomi Mi BluetoothLE Temperature and Humidity sensor.



## Functionality 
It supports reading the different measurements from the sensor
- temperature
- humidity
- battery level

To use this library you will need a Bluetooth Low Energy dongle attached to your computer. You will also need a
Xiaomi Mi Temperature and Humidity sensor. 

To use with home-assistant.io, implement the following GIST in HA:
https://gist.github.com/ratcashdev/28253bb2c220788e4961f213fe87ff33

## Backends
This sensor relies on the btlewrap library to provide a unified interface for various underlying btle implementations
* bluez tools (via a wrapper around gatttool)
* bluepy library

### bluez/gatttool wrapper
To use the bluez wrapper, you need to install the bluez tools on your machine. No additional python 
libraries are required. Some distrubutions moved the gatttool binary to a separate package. Make sure you have this 
binaray available on your machine.

Example to use the bluez/gatttool wrapper:
```python
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller
from btlewrap.gatttool import GatttoolBackend

poller = MiTempBtPoller('some mac address', GatttoolBackend)
```

### bluepy
To use the [bluepy](https://github.com/IanHarvey/bluepy) library you have to install it on your machine, in most cases this can be done via: 
```pip3 install bluepy``` 

Example to use the bluepy backend:
```python
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller
from btlewrap.bluepy import BluepyBackend

poller = MiTempBtPoller('some mac address', BluepyBackend)
```

### pygatt
This device needs notification support from the underlying backend in btlewrap. 
Currently only Gatttool or Bluepy provide this possibility. Pygatt is therefore not supported.
PRs to enhance btlewrap library's pygatt support should be directed to: https://github.com/ChristianKuehnel/btlewrap


## Conttributing
please have a look at [CONTRIBUTING.md](CONTRIBUTING.md)

----

## Projects Depending on `mitemp_bt`

https://github.com/home-assistant/home-assistant
