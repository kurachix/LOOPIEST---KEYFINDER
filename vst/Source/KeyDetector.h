#pragma once

#include <vector>
#include <string>
#include <array>
#include <cmath>
#include <algorithm>

namespace loopiest
{

struct KeyResult
{
    std::string keyName;        // e.g. "A Minor"
    std::string camelot;        // e.g. "8A"
    std::string scaleType;      // "Minor" or "Major"
    float confidence;           // 0.0 to 1.0
    float tuningHz;             // e.g. 440.0f
    std::array<float, 12> chromaProfile; // 12 pitch classes (C, C#, ..., B)
    std::vector<std::pair<std::string, float>> noteRanking; // Ranked dominant notes
};

class KeyDetector
{
public:
    KeyDetector();
    ~KeyDetector() = default;

    // Analyze 12-dimensional chroma vector and return detected key result
    KeyResult detectFromChroma(const std::array<float, 12>& chroma, float sampleRate = 44100.0f, float dominantFreq = 440.0f);

    // Helper: Map note index (0..11) to name (0 = C, 9 = A)
    static std::string getNoteName(int index);

    // Helper: Convert musical key to Camelot notation
    static std::string toCamelot(const std::string& keyName);

    // Helper: Calculate tuning frequency offset from 440Hz reference
    static float calculateTuning(float dominantPeakFreq);

private:
    // Krumhansl-Schmuckler cognitive pitch profile vectors (Major & Minor)
    std::array<float, 12> majorProfile;
    std::array<float, 12> minorProfile;

    void initProfiles();
    float correlation(const std::array<float, 12>& x, const std::array<float, 12>& y);
};

} // namespace loopiest
