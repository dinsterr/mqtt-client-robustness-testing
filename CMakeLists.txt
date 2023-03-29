cmake_minimum_required(VERSION 3.18.4)
project(fuzzing_targets C)
set(CMAKE_C_STANDARD 11)
# In case we want to build the library locally from the releases at: https://github.com/eclipse/paho.mqtt.c/releases
# (requires the include and lib folders)
list(APPEND CMAKE_PREFIX_PATH "./paho-mqtt")

find_package(eclipse-paho-mqtt-c REQUIRED)

add_executable(fuzzing_targets main.c)

target_link_libraries(fuzzing_targets eclipse-paho-mqtt-c::paho-mqtt3c)
