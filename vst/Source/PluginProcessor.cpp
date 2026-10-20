#include "PluginProcessor.h"
#include "PluginEditor.h"
#include <thread>

LoopiestAudioProcessor::LoopiestAudioProcessor()
    : AudioProcessor(BusesProperties().withInput("Input", juce::AudioChannelSet::stereo(), true)
                                      .withOutput("Output", juce::AudioChannelSet::stereo(), true)),
      forwardFFT(fftOrder),
      window(fftSize, juce::dsp::WindowingFunction<float>::hann)
{
    formatManager.registerBasicFormats();
    std::fill(fftData.begin(), fftData.end(), 0.0f);
    std::fill(fifo.begin(), fifo.end(), 0.0f);

    currentKeyResult.keyName = "WAITING...";
    currentKeyResult.camelot = "--";
    currentKeyResult.tuningHz = 440.0f;
    currentBpmResult.bpm = 120.0f;
}

LoopiestAudioProcessor::~LoopiestAudioProcessor()
{
}

const juce::String LoopiestAudioProcessor::getName() const
{
    return "LOOPIEST KEYFINDER";
}

bool LoopiestAudioProcessor::acceptsMidi() const { return false; }
bool LoopiestAudioProcessor::producesMidi() const { return false; }
bool LoopiestAudioProcessor::isMidiEffect() const { return false; }
double LoopiestAudioProcessor::getTailLengthSeconds() const { return 0.0; }

int LoopiestAudioProcessor::getNumPrograms() { return 1; }
int LoopiestAudioProcessor::getCurrentProgram() { return 0; }
void LoopiestAudioProcessor::setCurrentProgram(int) {}
const juce::String LoopiestAudioProcessor::getProgramName(int) { return {}; }
void LoopiestAudioProcessor::changeProgramName(int, const juce::String&) {}

void LoopiestAudioProcessor::prepareToPlay(double sampleRate, int samplesPerBlock)
{
    bpmDetector.reset();
    fifoIndex = 0;
    nextFFTBlockReady = false;
}

void LoopiestAudioProcessor::releaseResources()
{
}

bool LoopiestAudioProcessor::isBusesLayoutSupported(const BusesLayout& layouts) const
{
    if (layouts.getMainOutputChannelSet() != juce::AudioChannelSet::mono()
     && layouts.getMainOutputChannelSet() != juce::AudioChannelSet::stereo())
        return false;

    if (layouts.getMainOutputChannelSet() != layouts.getMainInputChannelSet())
        return false;

    return true;
}

void LoopiestAudioProcessor::processBlock(juce::AudioBuffer<float>& buffer, juce::MidiBuffer&)
{
    juce::ScopedNoDenormals noDenormals;
    auto totalNumInputChannels  = getTotalNumInputChannels();
    auto totalNumOutputChannels = getTotalNumOutputChannels();

    for (auto i = totalNumInputChannels; i < totalNumOutputChannels; ++i)
        buffer.clear(i, 0, buffer.getNumSamples());

    const int numSamples = buffer.getNumSamples();
    if (numSamples == 0)
        return;

    // Retrieve host tempo from FL Studio transport
    float hostBpm = 0.0f;
    if (auto* playHead = getPlayHead())
    {
        if (auto pos = playHead->getPosition())
        {
            if (pos->getBpm().hasValue())
                hostBpm = static_cast<float>(*pos->getBpm());
        }
    }

    // Process BPM
    auto bpmRes = bpmDetector.processBuffer(buffer.getArrayOfReadPointers(), totalNumInputChannels, numSamples, static_cast<float>(getSampleRate()), hostBpm);
    {
        std::lock_guard<std::mutex> lock(dataMutex);
        currentBpmResult = bpmRes;
    }

    // Accumulate mono sum into FIFO for FFT pitch/chroma analysis
    const float* leftChannel = buffer.getReadPointer(0);
    const float* rightChannel = (totalNumInputChannels > 1) ? buffer.getReadPointer(1) : leftChannel;

    float rmsEnergy = 0.0f;

    for (int i = 0; i < numSamples; ++i)
    {
        float sample = 0.5f * (leftChannel[i] + rightChannel[i]);
        rmsEnergy += sample * sample;

        if (fifoIndex < fftSize)
        {
            fifo[fifoIndex++] = sample;
        }

        if (fifoIndex >= fftSize)
        {
            std::copy(fifo.begin(), fifo.end(), fftData.begin());
            std::fill(fftData.begin() + fftSize, fftData.end(), 0.0f);
            fifoIndex = 0;
            processFFTFrame();
        }
    }

    rmsEnergy = std::sqrt(rmsEnergy / numSamples);
    audioActive.store(rmsEnergy > 0.005f);
}

void LoopiestAudioProcessor::processFFTFrame()
{
    // Apply Hann window
    window.multiplyByWindowingInverse(fftData.data(), fftSize);

    // Compute FFT
    forwardFFT.performFrequencyOnlyForwardTransform(fftData.data());

    float sampleRate = static_cast<float>(getSampleRate());
    if (sampleRate <= 0.0f) sampleRate = 44100.0f;

    std::array<float, 12> chromaAccum;
    std::fill(chromaAccum.begin(), chromaAccum.end(), 0.0f);

    float maxMag = 0.0f;
    float peakFreq = 440.0f;

    // Analyze frequencies from 55 Hz (A1) to 3520 Hz (A7)
    int minBin = static_cast<int>(std::floor(55.0f * fftSize / sampleRate));
    int maxBin = static_cast<int>(std::ceil(3520.0f * fftSize / sampleRate));
    minBin = std::max(1, minBin);
    maxBin = std::min(fftSize / 2, maxBin);

    for (int bin = minBin; bin < maxBin; ++bin)
    {
        float mag = fftData[bin];
        if (mag > maxMag)
        {
            maxMag = mag;
            peakFreq = bin * sampleRate / fftSize;
        }

        float freq = bin * sampleRate / fftSize;
        if (freq > 0.0f)
        {
            float pitchMidi = 12.0f * std::log2(freq / 440.0f) + 69.0f;
            int pitchClass = (static_cast<int>(std::round(pitchMidi)) % 12 + 12) % 12;
            chromaAccum[pitchClass] += mag;
        }
    }

    auto keyRes = keyDetector.detectFromChroma(chromaAccum, sampleRate, peakFreq);

    {
        std::lock_guard<std::mutex> lock(dataMutex);
        currentKeyResult = keyRes;
    }
}

loopiest::KeyResult LoopiestAudioProcessor::getLatestKeyResult()
{
    std::lock_guard<std::mutex> lock(dataMutex);
    return currentKeyResult;
}

loopiest::BpmResult LoopiestAudioProcessor::getLatestBpmResult()
{
    std::lock_guard<std::mutex> lock(dataMutex);
    return currentBpmResult;
}

bool LoopiestAudioProcessor::isAudioDetected() const
{
    return audioActive.load();
}

bool LoopiestAudioProcessor::isAnalyzingFile() const
{
    return analyzingFile.load();
}

float LoopiestAudioProcessor::getFileAnalysisProgress() const
{
    return fileProgress.load();
}

void LoopiestAudioProcessor::analyzeAudioFile(const juce::File& file)
{
    if (!file.existsAsFile())
        return;

    analyzingFile.store(true);
    fileProgress.store(0.1f);

    // Run offline sample analysis on background worker thread
    std::thread([this, file]() {
        std::unique_ptr<juce::AudioFormatReader> reader(formatManager.createReaderFor(file));
        if (reader != nullptr)
        {
            int numSamples = static_cast<int>(reader->lengthInSamples);
            float sampleRate = static_cast<float>(reader->sampleRate);

            juce::AudioBuffer<float> tempBuffer(1, std::min(numSamples, static_cast<int>(sampleRate * 60))); // max 60s
            reader->read(&tempBuffer, 0, tempBuffer.getNumSamples(), 0, true, false);

            fileProgress.store(0.4f);

            // Copy to vector for BPM & Key analysis
            std::vector<float> samples(tempBuffer.getReadPointer(0), tempBuffer.getReadPointer(0) + tempBuffer.getNumSamples());

            auto fileBpm = bpmDetector.analyzeFileBuffer(samples, sampleRate);
            fileProgress.store(0.7f);

            // Compute Chroma from file frames
            std::array<float, 12> totalChroma;
            std::fill(totalChroma.begin(), totalChroma.end(), 0.0f);

            int frameSize = 4096;
            for (size_t i = 0; i + frameSize < samples.size(); i += frameSize / 2)
            {
                std::vector<float> frameData(frameSize * 2, 0.0f);
                std::copy(samples.begin() + i, samples.begin() + i + frameSize, frameData.begin());
                window.multiplyByWindowingInverse(frameData.data(), frameSize);
                forwardFFT.performFrequencyOnlyForwardTransform(frameData.data());

                for (int bin = 10; bin < frameSize / 2; ++bin)
                {
                    float mag = frameData[bin];
                    float freq = bin * sampleRate / frameSize;
                    if (freq >= 55.0f && freq <= 3520.0f)
                    {
                        float pitchMidi = 12.0f * std::log2(freq / 440.0f) + 69.0f;
                        int pitchClass = (static_cast<int>(std::round(pitchMidi)) % 12 + 12) % 12;
                        totalChroma[pitchClass] += mag;
                    }
                }
            }

            auto fileKey = keyDetector.detectFromChroma(totalChroma, sampleRate, 440.0f);

            {
                std::lock_guard<std::mutex> lock(dataMutex);
                currentKeyResult = fileKey;
                currentBpmResult = fileBpm;
            }

            fileProgress.store(1.0f);
        }

        analyzingFile.store(false);
    }).detach();
}

bool LoopiestAudioProcessor::hasEditor() const { return true; }

juce::AudioProcessorEditor* LoopiestAudioProcessor::createEditor()
{
    return new LoopiestAudioProcessorEditor(*this);
}

void LoopiestAudioProcessor::getStateInformation(juce::MemoryBlock&) {}
void LoopiestAudioProcessor::setStateInformation(const void*, int) {}

// Plugin creation factory function for VST3
juce::AudioProcessor* JUCE_CALLTYPE createPluginFilter()
{
    return new LoopiestAudioProcessor();
}
