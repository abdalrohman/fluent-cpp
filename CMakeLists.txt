cmake_minimum_required(VERSION 3.14)
project(fluent_icons LANGUAGES CXX)

# Interface library for Dear ImGui Fluent System Icons bindings
add_library(fluent_icons_imgui INTERFACE)
add_library(fluent_icons::imgui ALIAS fluent_icons_imgui)

target_include_directories(fluent_icons_imgui INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

target_compile_features(fluent_icons_imgui INTERFACE cxx_std_17)
