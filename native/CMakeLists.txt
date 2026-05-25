cmake_minimum_required(VERSION 3.20)

project(chevel_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(Python3 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(chevel_native chevel_native.cpp)

target_compile_definitions(chevel_native PRIVATE CHEVEL_NATIVE_VERSION="0.1.0")

set_target_properties(chevel_native PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/.."
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/.."
)

if (MSVC)
    target_compile_options(chevel_native PRIVATE /W4 /permissive-)
else()
    target_compile_options(chevel_native PRIVATE -Wall -Wextra -Wpedantic)
endif()

