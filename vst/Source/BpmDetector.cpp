#include "BpmDetector.h"
#include <numeric>

namespace loopiest
{

BpmDetector::BpmDetector()
    : bufferCount(0)
{
    reset();
}

void BpmDetector::reset()
{
    onsetHistory.clear();
    prevMagnitude.clear();
    bufferCount = 0;
}

BpmResult BpmDetector::processBuffer(const float* const* channelData, int numChannels, int numSamples, float sampleRate, float hostBpm)
{
    BpmResult res;
    res.isHostSynced = false;
    res.confidence = 0.5f;

    // If FL Studio host provides an active valid BPM (> 30.0 and < 350.0), prioritize host sync
    if (hostBpm >= 40.0f && hostBpm <= 300.0f)
    {
        res.bpm = std::round(hostBpm * 10.0f) / 10.0f;
        res.isHostSynced = true;
        res.confidence = 1.0f;
        return res;
    }

    // Compute simple energy flux for incoming buffer
    float currentEnergy = 0.0f;
    for (int ch = 0; ch < numChannels; ++ch)
    {
        if (channelData[ch] != nullptr)
        {
            for (int i = 0; i < numSamples; ++i)
            {
                float s = channelData[ch][i];
                currentEnergy += s * s;
            }
        }
    }

    currentEnergy = std::sqrt(currentEnergy / std::max(1, numSamples * numChannels));
    onsetHistory.push_back(currentEnergy);

    // Keep rolling window of ~8 seconds of onsets
    float hopTime = static_cast<float>(numSamples) / sampleRate;
    size_t maxHistory = static_cast<size_t>(8.0f / hopTime);
    if (onsetHistory.size() > maxHistory)
        onsetHistory.erase(onsetHistory.begin(), onsetHistory.begin() + (onsetHistory.size() - maxHistory));

    if (onsetHistory.size() > static_cast<size_t>(2.0f / hopTime))
    {
        res.bpm = estimateBpmFromOnsets(onsetHistory, hopTime);
        res.confidence = 0.8f;
    }
    else
    {
        res.bpm = 120.0f; // Default standby
        res.confidence = 0.2f;
    }

    return res;
}

float BpmDetector::estimateBpmFromOnsets(const std::vector<float>& onsets, float hopTime)
{
    if (onsets.size() < 16 || hopTime <= 0.0f)
        return 120.0f;

    // Autocorrelation over BPM range 70 to 180 BPM
    float bestCorr = -1.0f;
    float bestBpm = 120.0f;

    for (float bpm = 70.0f; bpm <= 180.0f; bpm += 0.5f)
    {
        float periodSec = 60.0f / bpm;
        int lag = static_cast<int>(std::round(periodSec / hopTime));

        if (lag <= 0 || lag >= static_cast<int>(onsets.size()))
            continue;

        float sum = 0.0f;
        int count = 0;
        for (size_t i = lag; i < onsets.size(); ++i)
        {
            sum += onsets[i] * onsets[i - lag];
            count++;
        }

        if (count > 0)
        {
            float corr = sum / count;
            if (corr > bestCorr)
            {
                bestCorr = corr;
                bestBpm = bpm;
            }
        }
    }

    return std::round(bestBpm * 10.0f) / 10.0f;
}

BpmResult BpmDetector::analyzeFileBuffer(const std::vector<float>& audioSamples, float sampleRate)
{
    BpmResult res;
    res.isHostSynced = false;
    res.bpm = 120.0f;
    res.confidence = 0.85f;

    if (audioSamples.empty() || sampleRate <= 0.0f)
        return res;

    // Divide samples into 1024-sample frames (hop 512)
    const int hopSize = 512;
    float hopTime = static_cast<float>(hopSize) / sampleRate;
    std::vector<float> fileOnsets;

    float prevFrameEnergy = 0.0f;
    for (size_t i = 0; i + hopSize < audioSamples.size(); i += hopSize)
    {
        float energy = 0.0f;
        for (int j = 0; j < hopSize; ++j)
        {
            float s = audioSamples[i + j];
            energy += s * s;
        }
        energy = std::sqrt(energy / hopSize);

        // Half-wave rectified flux
        float flux = std::max(0.0f, energy - prevFrameEnergy);
        fileOnsets.push_back(flux);
        prevFrameEnergy = energy;
    }

    res.bpm = estimateBpmFromOnsets(fileOnsets, hopTime);
    return res;
}

} // namespace loopiest
