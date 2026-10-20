#pragma once

#include <juce_audio_processors/juce_audio_processors.h>
#include <juce_dsp/juce_dsp.h>
#include <juce_audio_formats/juce_audio_formats.h>
#include <mutex>
#include <atomic>

#include "KeyDetector.h"
#include "BpmDetector.h"
#include "AuthManager.h"

class LoopiestAudioProcessor : public juce::AudioProcessor
{
public:
    LoopiestAudioProcessor();
    ~LoopiestAudioProcessor() override;

    void prepareToPlay(double sampleRate, int samplesPerBlock) override;
    void releaseResources() override;

    bool isBusesLayoutSupported(const BusesLayout& layouts) const override;

    void processBlock(juce::AudioBuffer<float>&, juce::MidiBuffer&) override;

    juce::AudioProcessorEditor* createEditor() override;
    bool hasEditor() const override;

    const juce::String getName() const override;

    bool acceptsMidi() const override;
    bool producesMidi() const override;
    bool isMidiEffect() const override;
    double getTailLengthSeconds() const override;

    int getNumPrograms() override;
    int getCurrentProgram() override;
    void setCurrentProgram(int index) override;
    const juce::String getProgramName(int index) override;
    void changeProgramName(int index, const juce::String& newName) override;

    void getStateInformation(juce::MemoryBlock& destData) override;
    void setStateInformation(const void* data, int sizeInBytes) override;

    // --- Thread-Safe Data Getters for the UI ---
    loopiest::KeyResult getLatestKeyResult();
    loopiest::BpmResult getLatestBpmResult();
    bool isAudioDetected() const;

    // --- Offline Analysis (for drag & drop loops from FL Studio) ---
    void analyzeAudioFile(const juce::File& file);
    bool isAnalyzingFile() const;
    float getFileAnalysisProgress() const;

private:
    static constexpr int fftOrder = 12; // 4096 points
    static constexpr int fftSize = 1 << fftOrder;

    juce::dsp::FFT forwardFFT;
    juce::dsp::WindowingFunction<float> window;

    std::array<float, fftSize * 2> fftData;
    std::array<float, fftSize> fifo;
    int fifoIndex = 0;
    bool nextFFTBlockReady = false;

    // Analysis Engines
    loopiest::KeyDetector keyDetector;
    loopiest::BpmDetector bpmDetector;

    // Thread Synchronization
    std::mutex dataMutex;
    loopiest::KeyResult currentKeyResult;
    loopiest::BpmResult currentBpmResult;
    std::atomic<bool> audioActive { false };
    std::atomic<bool> analyzingFile { false };
    std::atomic<float> fileProgress { 0.0f };

    // Format Manager for Drag-and-Drop files
    juce::AudioFormatManager formatManager;

    void processFFTFrame();

    JUCE_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(LoopiestAudioProcessor)
};
