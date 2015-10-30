# Copyright (c) 2015, Robin Deits
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the copyright holder nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.


include(CMakeParseArguments)


function(add_swig_python_module target i_file)
	# Parse our arguments and make sure we got the required ones
	set(options CPLUSPLUS)
	set(oneValueArgs)
	set(multiValueArgs INCLUDE_DIRS LINK_LIBRARIES SWIG_INCLUDE_DIRS DESTINATION)
	cmake_parse_arguments(swigpy "${options}" "${oneValueArgs}" "${multiValueArgs}" ${ARGN} )
	if (NOT target)
		message(FATAL_ERROR "Error using add_swig_python_module: Please provide a unique cmake target name as the first argument")
	endif()
	if (NOT i_file)
		message(FATAL_ERROR "Error using add_swig_python_module: Please provide the path to your .i file as the second argument")
	endif()

	# Find python and get its version number
	find_package(PythonInterp REQUIRED)
	set(PYVERSION "${PYTHON_VERSION_MAJOR}.${PYTHON_VERSION_MINOR}")

	if(APPLE)
		# Overload the PYTHON_INCLUDE_DIR and PYTHON_LIBRARY because, on OSX with a homebrew-provided python, cmake latches on to an old Apple-provided python install. 
		execute_process(COMMAND python${PYTHON_VERSION_MAJOR}-config --prefix
			OUTPUT_VARIABLE PYTHON_PREFIX
			OUTPUT_STRIP_TRAILING_WHITESPACE
			)
		if (PYTHON_VERSION_MAJOR GREATER 2)
			set(PYTHON_INCLUDE_DIR ${PYTHON_PREFIX}/include/python${PYVERSION}m)
		else()
			set(PYTHON_INCLUDE_DIR ${PYTHON_PREFIX}/include/python${PYVERSION})
		endif()

		set(PYTHON_LIBRARY ${PYTHON_PREFIX}/lib/libpython${PYVERSION}.dylib)
		# These variable settings will affect the behavior of find_package(PythonLibs)
	endif()

	# Load the swig macros
	if (NOT SWIG_EXECUTABLE)
		find_package(SWIG REQUIRED)
		include(DrakeUseSWIG)
	endif()

	# Find the numpy header paths and include them. This calls the FindNumPy.cmake file included in this repo. 
	find_package(NumPy REQUIRED)
	include_directories(${NUMPY_INCLUDE_DIRS})

	# Find the python libraries so that we can link against them.
	find_package( PythonLibs REQUIRED )
	include_directories( ${PYTHON_INCLUDE_DIRS} )

	# Include any source directories that swig will need to find our c++ header files
	foreach(dir IN LISTS swigpy_INCLUDE_DIRS)
		include_directories(${dir})
	endforeach(dir)

	# Tell SWIG that we're compiling a c++ (not c) file, and tell it to use python3 if appropriate. 
	if (swigpy_CPLUSPLUS)
		set(CPLUSPLUS ON)
	else()
		set(CPLUSPLUS OFF)
	endif()
	if (PYTHON_VERSION_MAJOR GREATER 2)
		set_source_files_properties(${i_file} PROPERTIES
			CPLUSPLUS ${CPLUSPLUS}
			SWIG_FLAGS "-py3"
			)
	else()
		set_source_files_properties(${i_file} PROPERTIES 
			CPLUSPLUS ${CPLUSPLUS})
	endif()

	# Tell swig to also look for .i interface files in these folders
	foreach(dir IN LISTS swigpy_SWIG_INCLUDE_DIRS)
		set(CMAKE_SWIG_FLAGS ${CMAKE_SWIG_FLAGS} "-I${dir}")
	endforeach(dir)

	# Tell swig to build python bindings for our target library and link them against the C++ library. 
	swig_add_module(${target} python ${i_file})
	swig_link_libraries(${target} ${swigpy_LINK_LIBRARIES} ${PYTHON_LIBRARIES})

	# Make sure the resulting library has the correct name, even if the cmake target has a different name
	set_target_properties(${SWIG_MODULE_${target}_REAL_NAME} PROPERTIES OUTPUT_NAME _${SWIG_GET_EXTRA_OUTPUT_FILES_module_basename})

	# Automatically install to the correct subfolder if the swig module has a "package" declared
	if (swigpy_package_name)
		string(REGEX REPLACE "\\." "/" swigpy_package_path ${swig_package_name})
	endif()

	foreach(dir IN LISTS swigpy_DESTINATION)
		install(TARGETS ${SWIG_MODULE_${target}_REAL_NAME} DESTINATION ${dir}/${swigpy_package_path})
		foreach(file IN LISTS swig_extra_generated_files)
			install(FILES ${file} DESTINATION ${dir}/${swigpy_package_path})
		endforeach(file)
	endforeach(dir)

	# Clean up
	set_source_files_properties(${i_file} PROPERTIES SWIG_FLAGS "")
endfunction()
