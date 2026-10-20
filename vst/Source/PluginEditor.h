#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_gui_basics/juce_gui_basics.h>
#include "PluginProcessor.h"

class LoopiestAudioProcessorEditor : public juce::AudioProcessorEditor,
                                     public juce::Timer,
                                     public juce::FileDragAndDropTarget
{
public:
    explicit LoopiestAudioProcessorEditor(LoopiestAudioProcessor&);
    ~LoopiestAudioProcessorEditor() override;

    void paint(juce::Graphics&) override;
    void resized() override;
    void timerCallback() override;

    // File Drag and Drop Support (Directly from FL Studio Browser)
    bool isInterestedInFileDrag(const juce::StringArray& files) override;
    void fileDragEnter(const juce::StringArray& files, int x, int y) override;
    void fileDragExit(const juce::StringArray& files) override;
    void filesDropped(const juce::StringArray& files, int x, int y) override;

private:
    LoopiestAudioProcessor& audioProcessor;

    // GUI Components
    juce::Label headerLabel;
    juce::Label keyDisplayLabel;
    juce::Label camelotBadgeLabel;
    juce::Label bpmBadgeLabel;
    juce::Label tuningBadgeLabel;
    juce::TextButton copyButton;
    juce::ProgressBar fileProgressBar;

    double progressValue = 0.0;
    bool isDragHovered = false;

    // Cached state
    std::string lastKey = "--";
    std::string lastCamelot = "--";
    float lastBpm = 120.0f;
    float lastTuning = 440.0f;
    std::vector<std::pair<std::string, float>> lastRanking;

    void copyResultToClipboard();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(LoopiestAudioProcessorEditor)
};
