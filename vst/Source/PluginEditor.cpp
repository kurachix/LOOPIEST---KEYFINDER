#include "PluginProcessor.h"
#include "PluginEditor.h"

LoopiestAudioProcessorEditor::LoopiestAudioProcessorEditor(LoopiestAudioProcessor& p)
    : AudioProcessorEditor(&p),
      audioProcessor(p),
      fileProgressBar(progressValue)
{
    setSize(480, 520);

    // Header Branding
    headerLabel.setText("@L8PIEST  |  KEYFINDER VST", juce::dontSendNotification);
    headerLabel.setFont(juce::Font(13.0f, juce::Font::bold));
    headerLabel.setColour(juce::Label::textColourId, juce::Colour(0xFF8A2BE2));
    headerLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(headerLabel);

    // Key Display Label
    keyDisplayLabel.setText("READY...", juce::dontSendNotification);
    keyDisplayLabel.setFont(juce::Font(32.0f, juce::Font::bold));
    keyDisplayLabel.setColour(juce::Label::textColourId, juce::Colours::white);
    keyDisplayLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(keyDisplayLabel);

    // Camelot Badge
    camelotBadgeLabel.setText("--", juce::dontSendNotification);
    camelotBadgeLabel.setFont(juce::Font(18.0f, juce::Font::bold));
    camelotBadgeLabel.setColour(juce::Label::textColourId, juce::Colour(0xFF00E676));
    camelotBadgeLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(camelotBadgeLabel);

    // BPM Badge
    bpmBadgeLabel.setText("120.0 BPM", juce::dontSendNotification);
    bpmBadgeLabel.setFont(juce::Font(14.0f, juce::Font::bold));
    bpmBadgeLabel.setColour(juce::Label::textColourId, juce::Colour(0xFFC084FC));
    bpmBadgeLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(bpmBadgeLabel);

    // Tuning Badge
    tuningBadgeLabel.setText("440.0 Hz", juce::dontSendNotification);
    tuningBadgeLabel.setFont(juce::Font(14.0f, juce::Font::bold));
    tuningBadgeLabel.setColour(juce::Label::textColourId, juce::Colour(0xFFA0A0B8));
    tuningBadgeLabel.setJustificationType(juce::Justification::centred);
    addAndMakeVisible(tuningBadgeLabel);

    // Copy Button
    copyButton.setButtonText("COPIAR INFORMACOES");
    copyButton.setColour(juce::TextButton::buttonColourId, juce::Colour(0xFF2D0B5A));
    copyButton.setColour(juce::TextButton::textColourOffId, juce::Colours::white);
    copyButton.onClick = [this]() { copyResultToClipboard(); };
    addAndMakeVisible(copyButton);

    // Progress Bar (for offline loop analysis)
    fileProgressBar.setColour(juce::ProgressBar::foregroundColourId, juce::Colour(0xFF8A2BE2));
    fileProgressBar.setColour(juce::ProgressBar::backgroundColourId, juce::Colour(0xFF14141E));
    fileProgressBar.setVisible(false);
    addAndMakeVisible(fileProgressBar);

    // Refresh GUI at 30 FPS
    startTimerHz(30);
}

LoopiestAudioProcessorEditor::~LoopiestAudioProcessorEditor()
{
    stopTimer();
}

void LoopiestAudioProcessorEditor::timerCallback()
{
    auto keyRes = audioProcessor.getLatestKeyResult();
    auto bpmRes = audioProcessor.getLatestBpmResult();
    bool isAnalyzing = audioProcessor.isAnalyzingFile();

    if (isAnalyzing)
    {
        fileProgressBar.setVisible(true);
        progressValue = audioProcessor.getFileAnalysisProgress();
    }
    else
    {
        fileProgressBar.setVisible(false);
    }

    if (keyRes.keyName != lastKey || keyRes.camelot != lastCamelot || bpmRes.bpm != lastBpm || keyRes.tuningHz != lastTuning)
    {
        lastKey = keyRes.keyName;
        lastCamelot = keyRes.camelot;
        lastBpm = bpmRes.bpm;
        lastTuning = keyRes.tuningHz;
        lastRanking = keyRes.noteRanking;

        keyDisplayLabel.setText(juce::String(lastKey).toUpperCase(), juce::dontSendNotification);
        camelotBadgeLabel.setText(juce::String(lastCamelot), juce::dontSendNotification);

        juce::String bpmText = juce::String(lastBpm, 1) + " BPM";
        if (bpmRes.isHostSynced)
            bpmText += " (SYNC)";
        bpmBadgeLabel.setText(bpmText, juce::dontSendNotification);

        tuningBadgeLabel.setText(juce::String(lastTuning, 1) + " Hz", juce::dontSendNotification);

        repaint();
    }
}

void LoopiestAudioProcessorEditor::paint(juce::Graphics& g)
{
    // Background gradient
    juce::ColourGradient bgGradient(juce::Colour(0xFF0E0A1A), 0, 0,
                                   juce::Colour(0xFF07070A), 0, static_cast<float>(getHeight()), false);
    g.setGradientFill(bgGradient);
    g.fillAll();

    // Window Outer Border
    g.setColour(juce::Colour(0xFF2D0B5A));
    g.drawRoundedRectangle(getLocalBounds().toFloat().reduced(4.0f), 12.0f, 1.5f);

    // Central Key Card
    juce::Rectangle<float> keyCard(24.0f, 50.0f, static_cast<float>(getWidth() - 48), 160.0f);
    g.setColour(juce::Colour(0xFF120E22));
    g.fillRoundedRectangle(keyCard, 14.0f);

    // Card Glow Border
    g.setColour(juce::Colour(0xFF8A2BE2));
    g.drawRoundedRectangle(keyCard, 14.0f, 1.8f);

    // Live Audio Indicator dot
    bool active = audioProcessor.isAudioDetected();
    g.setColour(active ? juce::Colour(0xFF00E676) : juce::Colour(0xFF55556E));
    g.fillEllipse(44.0f, 66.0f, 10.0f, 10.0f);

    // Note Distribution Bars Card
    juce::Rectangle<float> rankingCard(24.0f, 222.0f, static_cast<float>(getWidth() - 48), 130.0f);
    g.setColour(juce::Colour(0xFF0F0B1A));
    g.fillRoundedRectangle(rankingCard, 12.0f);
    g.setColour(juce::Colour(0xFF23123B));
    g.drawRoundedRectangle(rankingCard, 12.0f, 1.0f);

    g.setColour(juce::Colour(0xFF8A2BE2));
    g.setFont(juce::Font(11.0f, juce::Font::bold));
    g.drawText("RANKING DE NOTAS DOMINANTES", 38, 230, getWidth() - 76, 18, juce::Justification::centredLeft);

    // Draw top 5 note bars
    int barY = 254;
    int maxBars = std::min(5, static_cast<int>(lastRanking.size()));
    for (int i = 0; i < maxBars; ++i)
    {
        const auto& item = lastRanking[i];

        // Note Name
        g.setColour(juce::Colours::white);
        g.setFont(juce::Font(12.0f, juce::Font::bold));
        g.drawText(item.first, 38, barY, 30, 14, juce::Justification::centredLeft);

        // Bar background
        float barX = 74.0f;
        float barWidth = static_cast<float>(getWidth() - 170);
        g.setColour(juce::Colour(0xFF1E1535));
        g.fillRoundedRectangle(barX, static_cast<float>(barY + 2), barWidth, 10.0f, 4.0f);

        // Bar fill
        float fillWidth = std::clamp((item.second / 35.0f) * barWidth, 4.0f, barWidth);
        g.setColour(i == 0 ? juce::Colour(0xFF00E676) : juce::Colour(0xFF8A2BE2));
        g.fillRoundedRectangle(barX, static_cast<float>(barY + 2), fillWidth, 10.0f, 4.0f);

        // Percentage label
        g.setColour(juce::Colour(0xFFA0A0B8));
        g.setFont(juce::Font(11.0f, juce::Font::plain));
        g.drawText(juce::String(item.second, 1) + "%", getWidth() - 86, barY, 48, 14, juce::Justification::centredRight);

        barY += 19;
    }

    // Drag and Drop Zone Card
    juce::Rectangle<float> dropZone(24.0f, 362.0f, static_cast<float>(getWidth() - 48), 84.0f);
    g.setColour(isDragHovered ? juce::Colour(0xFF221538) : juce::Colour(0xFF0E0E16));
    g.fillRoundedRectangle(dropZone, 12.0f);

    g.setColour(isDragHovered ? juce::Colour(0xFF00E676) : juce::Colour(0xFF4A1584));
    float dashPattern[] = { 6.0f, 4.0f };
    g.drawDashedRectangle(dropZone, 12.0f, dashPattern, 2, 1.5f);

    g.setColour(isDragHovered ? juce::Colour(0xFF00E676) : juce::Colour(0xFF8A2BE2));
    g.setFont(juce::Font(13.0f, juce::Font::bold));
    g.drawText("ARRASTE SAMPLES OU LOOPS DO FL STUDIO AQUI", 24, 382, getWidth() - 48, 20, juce::Justification::centred);

    g.setColour(juce::Colour(0xFF7E7E98));
    g.setFont(juce::Font(11.0f, juce::Font::plain));
    g.drawText("Ou reproduza o audio no Mixer para deteccao em tempo real", 24, 404, getWidth() - 48, 18, juce::Justification::centred);
}

void LoopiestAudioProcessorEditor::resized()
{
    headerLabel.setBounds(0, 16, getWidth(), 24);

    keyDisplayLabel.setBounds(30, 75, getWidth() - 60, 44);

    // Badges inside keyCard
    int badgeY = 145;
    int badgeW = 100;
    int badgeH = 28;
    int totalW = badgeW * 3 + 20;
    int startX = (getWidth() - totalW) / 2;

    camelotBadgeLabel.setBounds(startX, badgeY, badgeW, badgeH);
    bpmBadgeLabel.setBounds(startX + badgeW + 10, badgeY, badgeW, badgeH);
    tuningBadgeLabel.setBounds(startX + (badgeW + 10) * 2, badgeY, badgeW, badgeH);

    copyButton.setBounds(34, 458, getWidth() - 68, 40);
    fileProgressBar.setBounds(24, 348, getWidth() - 48, 8);
}

bool LoopiestAudioProcessorEditor::isInterestedInFileDrag(const juce::StringArray& files)
{
    for (const auto& f : files)
    {
        juce::String ext = juce::File(f).getFileExtension().toLowerCase();
        if (ext == ".wav" || ext == ".mp3" || ext == ".flac" || ext == ".aif" || ext == ".aiff" || ext == ".ogg")
            return true;
    }
    return false;
}

void LoopiestAudioProcessorEditor::fileDragEnter(const juce::StringArray&, int, int)
{
    isDragHovered = true;
    repaint();
}

void LoopiestAudioProcessorEditor::fileDragExit(const juce::StringArray&)
{
    isDragHovered = false;
    repaint();
}

void LoopiestAudioProcessorEditor::filesDropped(const juce::StringArray& files, int, int)
{
    isDragHovered = false;
    repaint();

    if (!files.isEmpty())
    {
        juce::File audioFile(files[0]);
        audioProcessor.analyzeAudioFile(audioFile);
    }
}

void LoopiestAudioProcessorEditor::copyResultToClipboard()
{
    juce::String info = lastKey + " (" + lastCamelot + ") - " + juce::String(lastBpm, 1) + " BPM - " + juce::String(lastTuning, 1) + "Hz";
    juce::SystemClipboard::copyTextToClipboard(info);

    copyButton.setButtonText("COPIADO COM SUCESSO!");
    juce::Timer::callAfterDelay(1500, [this]() {
        copyButton.setButtonText("COPIAR INFORMACOES");
    });
}
