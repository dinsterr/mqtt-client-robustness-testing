Built with JetBrains CLion IDE via default build:
```
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_MAKE_PROGRAM=/home/dfs/.local/share/JetBrains/Toolbox/apps/CLion/ch-0/223.8836.42/bin/ninja/li
nux/x64/ninja -G Ninja -S /home/dfs/CLionProjects/fuzzing-target -B /home/dfs/CLionProjects/fuzzing-target/cmake-build-debug

cmake --build /home/dfs/CLionProjects/fuzzing-target/cmake-build-debug
```

Executed with
```
./fuzzing-target -a 127.0.0.1 -p 8080 -t foo -q 0
```

The paho library does not need to be installed in the system.
It will be fetched from the ./paho-mqtt sub directory.
Place the include and lib folders of the official release at https://github.com/eclipse/paho.mqtt.c/releases into the paho-mqtt folder.
