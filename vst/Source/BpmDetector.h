#pragma once

#include <vector>
#include <cmath>
#include <algorithm>

namespace loopiest
{

struct BpmResult
{
    float bpm;             // Detected tempo (e.g. 140.0)
    float confidence;      // Reliability 0.0 to 1.0
    bool isHostSynced;     // True if synced from FL Studio transport
};

class BpmDetector
{
public:
    BpmDetector();
    ~BpmDetector() = default;

    // Reset internal onset history
    void reset();

    // Process a block of audio samples and return current estimated BPM
    BpmResult processBuffer(const float* const* channelData, int numChannels, int numSamples, float sampleRate, float hostBpm = 0.0f);

    // Full offline BPM detection for drag-and-dropped audio files
    BpmResult analyzeFileBuffer(const std::vector<float>& audioSamples, float sampleRate);

private:
    std::vector<float> onsetHistory;
    std::vector<float> prevMagnitude;
    int bufferCount;

    float estimateBpmFromOnsets(const std::vector<float>& onsets, float hopTime);
};

} // namespace loopiest
