Built with JetBrains CLion IDE via:
```
cmake -DCMAKE_BUILD_TYPE=Debug -DCMAKE_MAKE_PROGRAM=/home/dfs/.local/share/JetBrains/Toolbox/apps/CLion/ch-0/223.8836.42/bin/ninja/li
nux/x64/ninja -G Ninja -S /home/dfs/CLionProjects/fuzzing_targets -B /home/dfs/CLionProjects/fuzzing_targets/cmake-build-debug; cmake --build /home/dfs/CLionProjects/fuzzing_targets/cmake-build-debug
```

Executed with
```
./fuzzing_targets -a 127.0.0.1 -p 8080 -t foo -q 1
```