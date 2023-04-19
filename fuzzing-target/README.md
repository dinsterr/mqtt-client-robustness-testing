# fuzzing-target
An MQTT client with buffer overflow and command injection vulnerabilities.
Built with the examples from: https://github.com/eclipse/paho.mqtt.c/releases

Build:
```
# cd fuzzing-target
# LD_LIBRARY_PATH=. cmake .
# make
```

The paho library does not need to be installed in the system.
It is fetched from the ./paho-mqtt sub directory with the current `CMakeLists.txt`.
Place the `include` and `lib` folders of the official release at https://github.com/eclipse/paho.mqtt.c/releases into the `paho-mqtt` folder.
(Exact version used for our experiments was: https://github.com/eclipse/paho.mqtt.c/releases/download/v1.3.12/Eclipse-Paho-MQTT-C-1.3.12-Linux.tar.gz.zip)

Executed with:
```
# ./fuzzing-target -a 127.0.0.1 -p 8080 -t foo -q 0
```

Options:
- `a`: Address of the broker
- `p`: Port of the broker
- `t`: MQTT topic to subscribe to
- `q`: MQTT QoS behavior

