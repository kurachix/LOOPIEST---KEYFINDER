#pragma once

#include <vector>
#include <string>
#include <array>
#include <cmath>
#include <algorithm>
#include <numeric>

namespace loopiest
{

static constexpr int FFT_SIZE = 4096;

struct KeyInfo
{
    std::string keyName;
    std::string camelot;
    float confidence;
    float tuningHz;
    std::array<float, 12> chroma;
    std::vector<std::pair<std::string, float>> ranking;
};

class VstDsp
{
public:
    VstDsp()
    {
        initProfiles();
        initHannWindow();
        reset();
    }

    void reset()
    {
        fifoIndex = 0;
        std::fill(fifo.begin(), fifo.end(), 0.0f);
        std::fill(chromaAccum.begin(), chromaAccum.end(), 0.0f);
        audioActive = false;
        latestKey.keyName = "AGUARDANDO AUDIO...";
        latestKey.camelot = "--";
        latestKey.confidence = 0.0f;
        latestKey.tuningHz = 440.0f;
        latestBpm = 120.0f;
        isSynced = false;
    }

    void processSamples(const float* left, const float* right, int numSamples, float sampleRate, float hostBpm = 0.0f)
    {
        if (hostBpm >= 40.0f && hostBpm <= 300.0f)
        {
            latestBpm = std::round(hostBpm * 10.0f) / 10.0f;
            isSynced = true;
        }

        float energy = 0.0f;
        for (int i = 0; i < numSamples; ++i)
        {
            float s = 0.5f * (left[i] + (right ? right[i] : left[i]));
            energy += s * s;

            fifo[fifoIndex++] = s;
            if (fifoIndex >= FFT_SIZE)
            {
                runFftAnalysis(sampleRate);
                fifoIndex = 0;
            }
        }

        energy = std::sqrt(energy / std::max(1, numSamples));
        audioActive = (energy > 0.005f);
    }

    KeyInfo getLatestKey() const { return latestKey; }
    float getLatestBpm() const { return latestBpm; }
    bool isHostSynced() const { return isSynced; }
    bool isAudioPlaying() const { return audioActive; }

    // Offline file analysis (drag and drop)
    KeyInfo analyzeFileBuffer(const std::vector<float>& samples, float sampleRate, float& outBpm)
    {
        KeyInfo result;
        if (samples.empty() || sampleRate <= 0.0f)
            return result;

        std::array<float, 12> totalChroma;
        std::fill(totalChroma.begin(), totalChroma.end(), 0.0f);

        std::vector<float> frame(FFT_SIZE);
        for (size_t i = 0; i + FFT_SIZE < samples.size(); i += FFT_SIZE / 2)
        {
            for (int j = 0; j < FFT_SIZE; ++j)
                frame[j] = samples[i + j] * hannWindow[j];

            std::vector<float> mag(FFT_SIZE / 2);
            computeMagnitude(frame.data(), mag.data());

            for (int bin = 10; bin < FFT_SIZE / 2; ++bin)
            {
                float freq = bin * sampleRate / FFT_SIZE;
                if (freq >= 55.0f && freq <= 3520.0f)
                {
                    float midi = 12.0f * std::log2(freq / 440.0f) + 69.0f;
                    int pc = (static_cast<int>(std::round(midi)) % 12 + 12) % 12;
                    totalChroma[pc] += mag[bin];
                }
            }
        }

        result = detectKey(totalChroma, sampleRate, 440.0f);
        outBpm = estimateTempo(samples, sampleRate);
        return result;
    }

private:
    std::array<float, FFT_SIZE> fifo;
    int fifoIndex = 0;
    std::array<float, FFT_SIZE> hannWindow;
    std::array<float, 12> chromaAccum;
    std::array<float, 12> majorProfile;
    std::array<float, 12> minorProfile;

    KeyInfo latestKey;
    float latestBpm = 120.0f;
    bool isSynced = false;
    bool audioActive = false;

    void initProfiles()
    {
        majorProfile = { 6.35f, 2.23f, 3.48f, 2.33f, 4.38f, 4.09f, 2.52f, 5.19f, 2.39f, 3.66f, 2.29f, 2.88f };
        minorProfile = { 6.33f, 2.68f, 3.52f, 5.38f, 2.60f, 3.53f, 2.54f, 4.75f, 3.98f, 2.69f, 3.34f, 3.17f };
    }

    void initHannWindow()
    {
        for (int i = 0; i < FFT_SIZE; ++i)
            hannWindow[i] = 0.5f * (1.0f - std::cos(2.0f * 3.14159265358979323846f * i / (FFT_SIZE - 1)));
    }

    void computeMagnitude(const float* input, float* outputMag)
    {
        // In-place Cooley-Tukey Radix-2 FFT
        std::vector<float> real(FFT_SIZE);
        std::vector<float> imag(FFT_SIZE, 0.0f);
        for (int i = 0; i < FFT_SIZE; ++i)
            real[i] = input[i];

        // Bit reversal
        int j = 0;
        for (int i = 0; i < FFT_SIZE - 1; ++i)
        {
            if (i < j)
            {
                std::swap(real[i], real[j]);
                std::swap(imag[i], imag[j]);
            }
            int k = FFT_SIZE >> 1;
            while (k <= j)
            {
                j -= k;
                k >>= 1;
            }
            j += k;
        }

        // Cooley-Tukey computation
        for (int len = 2; len <= FFT_SIZE; len <<= 1)
        {
            float angle = -2.0f * 3.14159265358979323846f / len;
            float wlen_r = std::cos(angle);
            float wlen_i = std::sin(angle);
            for (int i = 0; i < FFT_SIZE; i += len)
            {
                float w_r = 1.0f;
                float w_i = 0.0f;
                for (int m = 0; m < len / 2; ++m)
                {
                    float u_r = real[i + m];
                    float u_i = imag[i + m];
                    float v_r = real[i + m + len / 2] * w_r - imag[i + m + len / 2] * w_i;
                    float v_i = real[i + m + len / 2] * w_i + imag[i + m + len / 2] * w_r;
                    real[i + m] = u_r + v_r;
                    imag[i + m] = u_i + v_i;
                    real[i + m + len / 2] = u_r - v_r;
                    imag[i + m + len / 2] = u_i - v_i;

                    float next_w_r = w_r * wlen_r - w_i * wlen_i;
                    float next_w_i = w_r * wlen_i + w_i * wlen_r;
                    w_r = next_w_r;
                    w_i = next_w_i;
                }
            }
        }

        // Magnitude
        for (int i = 0; i < FFT_SIZE / 2; ++i)
            outputMag[i] = std::sqrt(real[i] * real[i] + imag[i] * imag[i]);
    }

    void runFftAnalysis(float sampleRate)
    {
        std::vector<float> windowed(FFT_SIZE);
        for (int i = 0; i < FFT_SIZE; ++i)
            windowed[i] = fifo[i] * hannWindow[i];

        std::vector<float> mag(FFT_SIZE / 2);
        computeMagnitude(windowed.data(), mag.data());

        float peakMag = 0.0f;
        float peakFreq = 440.0f;

        for (int bin = 10; bin < FFT_SIZE / 2; ++bin)
        {
            float freq = bin * sampleRate / FFT_SIZE;
            if (freq >= 55.0f && freq <= 3520.0f)
            {
                float m = mag[bin];
                if (m > peakMag)
                {
                    peakMag = m;
                    peakFreq = freq;
                }

                float midi = 12.0f * std::log2(freq / 440.0f) + 69.0f;
                int pc = (static_cast<int>(std::round(midi)) % 12 + 12) % 12;
                chromaAccum[pc] = chromaAccum[pc] * 0.95f + m * 0.05f; // Exponential decay
            }
        }

        latestKey = detectKey(chromaAccum, sampleRate, peakFreq);
    }

    static std::string noteName(int idx)
    {
        static const char* names[12] = { "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B" };
        return names[(idx % 12 + 12) % 12];
    }

    static std::string toCamelot(const std::string& key)
    {
        if (key == "Ab Minor" || key == "G# Minor") return "1A";
        if (key == "B Major")                       return "1B";
        if (key == "Eb Minor" || key == "D# Minor") return "2A";
        if (key == "F# Major" || key == "Gb Major") return "2B";
        if (key == "Bb Minor" || key == "A# Minor") return "3A";
        if (key == "Db Major" || key == "C# Major") return "3B";
        if (key == "F Minor")                       return "4A";
        if (key == "Ab Major" || key == "G# Major") return "4B";
        if (key == "C Minor")                       return "5A";
        if (key == "Eb Major" || key == "D# Major") return "5B";
        if (key == "G Minor")                       return "6A";
        if (key == "Bb Major" || key == "A# Major") return "6B";
        if (key == "D Minor")                       return "7A";
        if (key == "F Major")                       return "7B";
        if (key == "A Minor")                       return "8A";
        if (key == "C Major")                       return "8B";
        if (key == "E Minor")                       return "9A";
        if (key == "G Major")                       return "9B";
        if (key == "B Minor")                       return "10A";
        if (key == "D Major")                       return "10B";
        if (key == "F# Minor" || key == "Gb Minor") return "11A";
        if (key == "A Major")                       return "11B";
        if (key == "C# Minor" || key == "Db Minor") return "12A";
        if (key == "E Major")                       return "12B";
        return "--";
    }

    KeyInfo detectKey(const std::array<float, 12>& chroma, float sampleRate, float peakFreq)
    {
        KeyInfo res;
        res.chroma = chroma;

        // Tuning detection
        float midi = 12.0f * std::log2(std::max(10.0f, peakFreq) / 440.0f) + 69.0f;
        int nearestMidi = static_cast<int>(std::round(midi));
        float dev = midi - static_cast<float>(nearestMidi);
        float tuning = 440.0f * std::pow(2.0f, dev / 12.0f);
        if (tuning < 415.0f || tuning > 465.0f) tuning = 440.0f;
        res.tuningHz = std::round(tuning * 10.0f) / 10.0f;

        float bestCorr = -100.0f;
        std::string bestKey = "C Major";

        for (int shift = 0; shift < 12; ++shift)
        {
            std::array<float, 12> rotMaj, rotMin;
            for (int i = 0; i < 12; ++i)
            {
                rotMaj[i] = majorProfile[(i - shift + 12) % 12];
                rotMin[i] = minorProfile[(i - shift + 12) % 12];
            }

            float cMaj = pearson(chroma, rotMaj);
            if (cMaj > bestCorr)
            {
                bestCorr = cMaj;
                bestKey = noteName(shift) + " Major";
            }

            float cMin = pearson(chroma, rotMin);
            if (cMin > bestCorr)
            {
                bestCorr = cMin;
                bestKey = noteName(shift) + " Minor";
            }
        }

        res.keyName = bestKey;
        res.camelot = toCamelot(bestKey);
        res.confidence = std::clamp((bestCorr + 1.0f) / 2.0f, 0.0f, 1.0f);

        // Note Ranking
        float total = std::accumulate(chroma.begin(), chroma.end(), 0.0f);
        res.ranking.clear();
        if (total > 1e-5f)
        {
            for (int i = 0; i < 12; ++i)
                res.ranking.emplace_back(noteName(i), (chroma[i] / total) * 100.0f);

            std::sort(res.ranking.begin(), res.ranking.end(), [](const auto& a, const auto& b) {
                return a.second > b.second;
            });
        }

        return res;
    }

    float pearson(const std::array<float, 12>& a, const std::array<float, 12>& b)
    {
        float ma = std::accumulate(a.begin(), a.end(), 0.0f) / 12.0f;
        float mb = std::accumulate(b.begin(), b.end(), 0.0f) / 12.0f;
        float num = 0.0f, da = 0.0f, db = 0.0f;
        for (int i = 0; i < 12; ++i)
        {
            float xa = a[i] - ma, xb = b[i] - mb;
            num += xa * xb;
            da += xa * xa;
            db += xb * xb;
        }
        float den = std::sqrt(da * db);
        return (den > 1e-8f) ? (num / den) : 0.0f;
    }

    float estimateTempo(const std::vector<float>& samples, float sampleRate)
    {
        const int hop = 512;
        float hopTime = static_cast<float>(hop) / sampleRate;
        std::vector<float> onsets;
        float prevE = 0.0f;

        for (size_t i = 0; i + hop < samples.size(); i += hop)
        {
            float e = 0.0f;
            for (int j = 0; j < hop; ++j) e += samples[i + j] * samples[i + j];
            e = std::sqrt(e / hop);
            onsets.push_back(std::max(0.0f, e - prevE));
            prevE = e;
        }

        float bestCorr = -1.0f;
        float bestBpm = 120.0f;
        for (float bpm = 70.0f; bpm <= 180.0f; bpm += 0.5f)
        {
            int lag = static_cast<int>(std::round((60.0f / bpm) / hopTime));
            if (lag <= 0 || lag >= static_cast<int>(onsets.size())) continue;
            float sum = 0.0f;
            int count = 0;
            for (size_t i = lag; i < onsets.size(); ++i)
            {
                sum += onsets[i] * onsets[i - lag];
                count++;
            }
            if (count > 0 && (sum / count) > bestCorr)
            {
                bestCorr = sum / count;
                bestBpm = bpm;
            }
        }
        return std::round(bestBpm * 10.0f) / 10.0f;
    }
};

} // namespace loopiest
