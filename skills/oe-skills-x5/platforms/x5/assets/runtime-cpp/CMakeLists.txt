cmake_minimum_required(VERSION 3.10)
project(x5_single_input_infer LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type")
set(X5_DNN_ROOT "" CACHE PATH "X5 Runtime dnn root containing include/ and lib/")

if(NOT X5_DNN_ROOT)
  message(FATAL_ERROR "Set -DX5_DNN_ROOT=/absolute/path/to/x5_aarch64/dnn")
endif()

add_executable(x5_single_input_infer main.cc)
target_include_directories(x5_single_input_infer PRIVATE "${X5_DNN_ROOT}/include")
target_link_directories(x5_single_input_infer PRIVATE "${X5_DNN_ROOT}/lib")
target_compile_options(x5_single_input_infer PRIVATE -Wall -Wextra -Werror -O3)
set_target_properties(x5_single_input_infer PROPERTIES LINK_FLAGS "-Wl,-unresolved-symbols=ignore-in-shared-libs")
target_link_libraries(x5_single_input_infer PRIVATE dnn pthread rt dl)
