#include "KeyDetector.h"
#include <unordered_map>
#include <numeric>

namespace loopiest
{

KeyDetector::KeyDetector()
{
    initProfiles();
}

void KeyDetector::initProfiles()
{
    // Krumhansl-Kessler / Temperley cognitive pitch profiles
    // Major: C, C#, D, D#, E, F, F#, G, G#, A, A#, B
    majorProfile = { 6.35f, 2.23f, 3.48f, 2.33f, 4.38f, 4.09f, 2.52f, 5.19f, 2.39f, 3.66f, 2.29f, 2.88f };
    minorProfile = { 6.33f, 2.68f, 3.52f, 5.38f, 2.60f, 3.53f, 2.54f, 4.75f, 3.98f, 2.69f, 3.34f, 3.17f };
}

float KeyDetector::correlation(const std::array<float, 12>& x, const std::array<float, 12>& y)
{
    float meanX = std::accumulate(x.begin(), x.end(), 0.0f) / 12.0f;
    float meanY = std::accumulate(y.begin(), y.end(), 0.0f) / 12.0f;

    float num = 0.0f;
    float denX = 0.0f;
    float denY = 0.0f;

    for (int i = 0; i < 12; ++i)
    {
        float dx = x[i] - meanX;
        float dy = y[i] - meanY;
        num += dx * dy;
        denX += dx * dx;
        denY += dy * dy;
    }

    float den = std::sqrt(denX * denY);
    if (den < 1e-8f)
        return 0.0f;

    return num / den;
}

std::string KeyDetector::getNoteName(int index)
{
    static const std::string noteNames[12] = {
        "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"
    };
    return noteNames[(index % 12 + 12) % 12];
}

std::string KeyDetector::toCamelot(const std::string& keyName)
{
    // Camelot Wheel Table (FL Studio / Mixed In Key standard)
    static const std::unordered_map<std::string, std::string> camelotMap = {
        // Minor (A)
        {"Ab Minor", "1A"}, {"G# Minor", "1A"},
        {"Eb Minor", "2A"}, {"D# Minor", "2A"},
        {"Bb Minor", "3A"}, {"A# Minor", "3A"},
        {"F Minor",  "4A"},
        {"C Minor",  "5A"},
        {"G Minor",  "6A"},
        {"D Minor",  "7A"},
        {"A Minor",  "8A"},
        {"E Minor",  "9A"},
        {"B Minor",  "10A"},
        {"F# Minor", "11A"}, {"Gb Minor", "11A"},
        {"C# Minor", "12A"}, {"Db Minor", "12A"},

        // Major (B)
        {"B Major",  "1B"},
        {"F# Major", "2B"}, {"Gb Major", "2B"},
        {"Db Major", "3B"}, {"C# Major", "3B"},
        {"Ab Major", "4B"}, {"G# Major", "4B"},
        {"Eb Major", "5B"}, {"D# Major", "5B"},
        {"Bb Major", "6B"}, {"A# Major", "6B"},
        {"F Major",  "7B"},
        {"C Major",  "8B"},
        {"G Major",  "9B"},
        {"D Major",  "10B"},
        {"A Major",  "11B"},
        {"E Major",  "12B"}
    };

    auto it = camelotMap.find(keyName);
    if (it != camelotMap.end())
        return it->second;

    return "--";
}

float KeyDetector::calculateTuning(float dominantPeakFreq)
{
    if (dominantPeakFreq <= 0.0f)
        return 440.0f;

    // Detect reference tuning A4 around 440 Hz (detecting 432 Hz vs 440 Hz vs 444 Hz)
    float midiNum = 12.0f * std::log2(dominantPeakFreq / 440.0f) + 69.0f;
    int nearestMidi = static_cast<int>(std::round(midiNum));
    float deviationSemitones = midiNum - static_cast<float>(nearestMidi);

    float tuning = 440.0f * std::pow(2.0f, deviationSemitones / 12.0f);
    if (tuning < 415.0f || tuning > 465.0f)
        return 440.0f;

    return std::round(tuning * 10.0f) / 10.0f;
}

KeyResult KeyDetector::detectFromChroma(const std::array<float, 12>& chroma, float sampleRate, float dominantFreq)
{
    KeyResult result;
    result.chromaProfile = chroma;
    result.tuningHz = calculateTuning(dominantFreq);

    float bestCorr = -100.0f;
    std::string bestKey = "C Major";
    std::string bestScale = "Major";

    // Test all 12 shifts for Major and Minor
    for (int shift = 0; shift < 12; ++shift)
    {
        std::array<float, 12> rotatedMajor;
        std::array<float, 12> rotatedMinor;

        for (int i = 0; i < 12; ++i)
        {
            rotatedMajor[i] = majorProfile[(i - shift + 12) % 12];
            rotatedMinor[i] = minorProfile[(i - shift + 12) % 12];
        }

        float corrMaj = correlation(chroma, rotatedMajor);
        if (corrMaj > bestCorr)
        {
            bestCorr = corrMaj;
            bestKey = getNoteName(shift) + " Major";
            bestScale = "Major";
        }

        float corrMin = correlation(chroma, rotatedMinor);
        if (corrMin > bestCorr)
        {
            bestCorr = corrMin;
            bestKey = getNoteName(shift) + " Minor";
            bestScale = "Minor";
        }
    }

    result.keyName = bestKey;
    result.scaleType = bestScale;
    result.camelot = toCamelot(bestKey);
    result.confidence = std::clamp((bestCorr + 1.0f) / 2.0f, 0.0f, 1.0f);

    // Compute Note Ranking (Percentages)
    float totalChroma = std::accumulate(chroma.begin(), chroma.end(), 0.0f);
    result.noteRanking.clear();

    if (totalChroma > 1e-6f)
    {
        for (int i = 0; i < 12; ++i)
        {
            float pct = (chroma[i] / totalChroma) * 100.0f;
            result.noteRanking.emplace_back(getNoteName(i), pct);
        }

        std::sort(result.noteRanking.begin(), result.noteRanking.end(),
                  [](const auto& a, const auto& b) {
                      return a.second > b.second;
                  });
    }

    return result;
}

} // namespace loopiest
