cmake_minimum_required(VERSION 3.20)

project(LOOPIEST_KEYFINDER_VST VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Enable automatic JUCE FetchContent so no local JUCE installation is required
include(FetchContent)

message(STATUS "[LOOPIEST VST] Baixando framework JUCE 8 oficial...")
FetchContent_Declare(
    JUCE
    GIT_REPOSITORY https://github.com/juce-framework/JUCE.git
    GIT_TAG        8.0.4
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(JUCE)

# Define JUCE VST3 / Standalone Audio Plugin
juce_add_plugin(LOOPIEST_KEYFINDER
    IS_SYNTH FALSE
    NEEDS_MIDI_INPUT FALSE
    NEEDS_MIDI_OUTPUT FALSE
    IS_MIDI_EFFECT FALSE
    EDITOR_WANTS_KEYBOARD_FOCUS TRUE
    COPY_PLUGIN_AFTER_BUILD TRUE
    PLUGIN_MANUFACTURER_CODE Lpst
    PLUGIN_CODE Lpst
    FORMATS VST3 Standalone
    PRODUCT_NAME "LOOPIEST KEYFINDER"
    COMPANY_NAME "LOOPIEST"
    COMPANY_WEBSITE "https://www.instagram.com/l8piest/"
    BUNDLE_ID "com.loopiest.keyfinder.vst3"
)

# Source files
target_sources(LOOPIEST_KEYFINDER
    PRIVATE
        Source/PluginProcessor.h
        Source/PluginProcessor.cpp
        Source/PluginEditor.h
        Source/PluginEditor.cpp
        Source/KeyDetector.h
        Source/KeyDetector.cpp
        Source/BpmDetector.h
        Source/BpmDetector.cpp
        Source/AuthManager.h
        Source/AuthManager.cpp
)

# Link essential JUCE modules
target_link_libraries(LOOPIEST_KEYFINDER
    PRIVATE
        juce::juce_audio_utils
        juce::juce_audio_processors
        juce::juce_dsp
        juce::juce_audio_formats
        juce::juce_gui_basics
        juce::juce_recommended_config_flags
        juce::juce_recommended_lto_flags
        juce::juce_recommended_warning_flags
)

# Binary copy target to system VST3 directory for FL Studio auto-detection
if (WIN32)
    set(VST3_INSTALL_PATH "$ENV{COMMONPROGRAMFILES}/VST3")
    add_custom_command(TARGET LOOPIEST_KEYFINDER_VST3 POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E make_directory "${VST3_INSTALL_PATH}"
        COMMAND ${CMAKE_COMMAND} -E copy_directory
            "$<TARGET_FILE_DIR:LOOPIEST_KEYFINDER_VST3>/../LOOPIEST KEYFINDER.vst3"
            "${VST3_INSTALL_PATH}/LOOPIEST KEYFINDER.vst3"
        COMMENT "[FL STUDIO AUTO-INSTALL] Instalando LOOPIEST KEYFINDER.vst3 em ${VST3_INSTALL_PATH}..."
    )
endif()
