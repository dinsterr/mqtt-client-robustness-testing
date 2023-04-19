# mqtt-client-robustness-testing

A framework to automatically test and monitor MQTT clients via generated PUBLISH messages.

This repository contains the code for the master’s thesis "Automated Robustness Testing of MQTT Clients via a Novel Fuzzing Framework" written by David Schrenk at the University of Passau (19.04.2023).

The goal of this project is to provide an automated testing framework for a wide range of MQTT clients.
It consists of: 
- `auto-mqtt-broker`: An MQTT broker written in Python that sends a list of generated PUBLISH packets to its subscribers.
- `mqtt-client-monitor`: A monitoring component written in Python that instruments the system under test and monitors its buffer output as well as its TCP connection to the broker.
- `fuzzing-target`: An MQTT client, written in C with the https://github.com/eclipse/paho.mqtt.c/ library to present a vulnerable system to illustrate the capabilities of the framework.

## auto-mqtt-broker
The core of the broker was written for a different thesis, which can be found here: https://github.com/babbadeckl/multilateral-security-mqtt
We adapted the code to include automated message generation.

- Built for Python 3.10.10. Install the requirements via `pip install -r requirements.txt` and run it with `python broker.py`
- Configure with `auto-mqtt-broker/broker.config`.
- Available message generators are located in `auto-mqtt-broker/broker/message_generators`. The files are loaded automatically by the `message_generator.py`. Look at the `hello_world.py` generator as a base for your own generator.

## mqtt-client-monitor
Monitoring component that starts the system under test and monitors `STDOUT`, `STDERR` buffers, the return code of the test subprocess and the TCP connection via a builtin TCP proxy.

- Built for Python 3.10.10. Run it with `python monitor.py`
- Configure with `mqtt-client-monitor/config.py`.
- Make sure that you have a broker running, otherwise the TCP proxy will fail with a socket connection error.

## fuzzing-target
Documentation of the C code can be found in the `fuzzing-target/README.md`.


