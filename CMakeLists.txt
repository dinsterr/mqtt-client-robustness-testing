cmake_minimum_required(VERSION 3.18.4)
project(fuzzing_targets C)
set(CMAKE_C_STANDARD 11)

find_package(eclipse-paho-mqtt-c REQUIRED)
add_executable(fuzzing_targets main.c)

target_link_libraries(fuzzing_targets eclipse-paho-mqtt-c::paho-mqtt3c)