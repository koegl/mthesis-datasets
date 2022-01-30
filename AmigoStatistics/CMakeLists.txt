cmake_minimum_required(VERSION 3.13.4)

project(AmigoStatistics)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "https://github.com/koegl/mthesis-datasets")
set(EXTENSION_CATEGORY "Informatics")
set(EXTENSION_CONTRIBUTORS "Fryderyk Kögl (TUM, BWH)")
set(EXTENSION_DESCRIPTION "AmigoStatistics is a Slicer extension to extract the data hierarchy of cases")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/koegl/SlicerMRUSLandmarking/main/misc/icon.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/koegl/SlicerMRUSLandmarking/main/misc/GUIpreview.png")
set(EXTENSION_DEPENDS "NA") # Specified as a list or "NA" if no dependencies

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(AmigoStatistics)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_GENERATE_CONFIG})
include(${Slicer_EXTENSION_CPACK})
