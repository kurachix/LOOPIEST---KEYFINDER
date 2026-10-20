#pragma once

#include <windows.h>
#include <gdiplus.h>
#include <string>
#include <vector>
#include <fstream>
#include "VstDsp.h"

#pragma comment(lib, "gdiplus.lib")

namespace loopiest
{

class VstGui
{
public:
    VstGui(VstDsp* dspPtr)
        : dsp(dspPtr), hwnd(NULL), isHovered(false), copyFeedbackTimer(0)
    {
        Gdiplus::GdiplusStartupInput gdiInput;
        Gdiplus::GdiplusStartup(&gdiToken, &gdiInput, NULL);
    }

    ~VstGui()
    {
        close();
        Gdiplus::GdiplusShutdown(gdiToken);
    }

    bool open(void* parentHwnd)
    {
        if (hwnd) return true;

        HINSTANCE hInstance = GetModuleHandle(NULL);
        WNDCLASSEX wc = { sizeof(WNDCLASSEX) };
        wc.lpfnWndProc = StaticWndProc;
        wc.hInstance = hInstance;
        wc.lpszClassName = TEXT("LoopiestKeyfinderVST");
        wc.hCursor = LoadCursor(NULL, IDC_ARROW);
        RegisterClassEx(&wc);

        hwnd = CreateWindowEx(
            0,
            TEXT("LoopiestKeyfinderVST"),
            TEXT("LOOPIEST KEYFINDER"),
            WS_CHILD | WS_VISIBLE | WS_CLIPCHILDREN,
            0, 0, 460, 500,
            (HWND)parentHwnd,
            NULL,
            hInstance,
            this
        );

        if (hwnd)
        {
            DragAcceptFiles(hwnd, TRUE);
            SetTimer(hwnd, 1, 33, NULL); // 30 FPS update timer
            return true;
        }
        return false;
    }

    void close()
    {
        if (hwnd)
        {
            KillTimer(hwnd, 1);
            DestroyWindow(hwnd);
            hwnd = NULL;
        }
    }

    HWND getHwnd() const { return hwnd; }

private:
    VstDsp* dsp;
    HWND hwnd;
    ULONG_PTR gdiToken;
    bool isHovered;
    int copyFeedbackTimer;

    static LRESULT CALLBACK StaticWndProc(HWND h, UINT msg, WPARAM wParam, LPARAM lParam)
    {
        VstGui* self = nullptr;
        if (msg == WM_NCCREATE)
        {
            CREATESTRUCT* cs = (CREATESTRUCT*)lParam;
            self = (VstGui*)cs->lpCreateParams;
            SetWindowLongPtr(h, GWLP_USERDATA, (LONG_PTR)self);
        }
        else
        {
            self = (VstGui*)GetWindowLongPtr(h, GWLP_USERDATA);
        }

        if (self)
            return self->handleMessage(h, msg, wParam, lParam);

        return DefWindowProc(h, msg, wParam, lParam);
    }

    LRESULT handleMessage(HWND h, UINT msg, WPARAM wParam, LPARAM lParam)
    {
        switch (msg)
        {
            case WM_TIMER:
                if (copyFeedbackTimer > 0)
                {
                    copyFeedbackTimer--;
                    if (copyFeedbackTimer == 0)
                        InvalidateRect(h, NULL, FALSE);
                }
                InvalidateRect(h, NULL, FALSE);
                return 0;

            case WM_PAINT:
            {
                PAINTSTRUCT ps;
                HDC hdc = BeginPaint(h, &ps);
                render(hdc);
                EndPaint(h, &ps);
                return 0;
            }

            case WM_ERASEBKGND:
                return 1; // Prevent flickering via double buffering

            case WM_LBUTTONDOWN:
            {
                int x = LOWORD(lParam);
                int y = HIWORD(lParam);
                // Copy button rect: (34, 440, 392, 38)
                if (x >= 34 && x <= 426 && y >= 440 && y <= 478)
                {
                    copyToClipboard();
                    copyFeedbackTimer = 45; // ~1.5s
                    InvalidateRect(h, NULL, FALSE);
                }
                return 0;
            }

            case WM_DROPFILES:
            {
                HDROP hDrop = (HDROP)wParam;
                TCHAR filePath[MAX_PATH];
                if (DragQueryFile(hDrop, 0, filePath, MAX_PATH))
                {
                    loadAndAnalyzeFile(filePath);
                }
                DragFinish(hDrop);
                InvalidateRect(h, NULL, FALSE);
                return 0;
            }
        }
        return DefWindowProc(h, msg, wParam, lParam);
    }

    void copyToClipboard()
    {
        if (!dsp) return;
        auto key = dsp->getLatestKey();
        float bpm = dsp->getLatestBpm();

        char text[256];
        snprintf(text, sizeof(text), "%s (%s) - %.1f BPM - %.1fHz",
                 key.keyName.c_str(), key.camelot.c_str(), bpm, key.tuningHz);

        if (OpenClipboard(hwnd))
        {
            EmptyClipboard();
            size_t len = strlen(text) + 1;
            HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, len);
            if (hMem)
            {
                memcpy(GlobalLock(hMem), text, len);
                GlobalUnlock(hMem);
                SetClipboardData(CF_TEXT, hMem);
            }
            CloseClipboard();
        }
    }

    void loadAndAnalyzeFile(const TCHAR* filePath)
    {
        std::ifstream file(filePath, std::ios::binary);
        if (!file.is_open()) return;

        // Simple RIFF WAV parser
        char header[44];
        file.read(header, 44);
        if (memcmp(header, "RIFF", 4) != 0 || memcmp(header + 8, "WAVE", 4) != 0)
            return;

        int numChannels = *reinterpret_cast<short*>(header + 22);
        int sampleRate = *reinterpret_cast<int*>(header + 24);
        int bitsPerSample = *reinterpret_cast<short*>(header + 34);

        if (numChannels <= 0 || sampleRate <= 0) return;

        std::vector<float> samples;
        if (bitsPerSample == 16)
        {
            std::vector<short> raw(sampleRate * numChannels * 45); // max 45s
            file.read(reinterpret_cast<char*>(raw.data()), raw.size() * sizeof(short));
            size_t readShorts = file.gcount() / sizeof(short);
            for (size_t i = 0; i + numChannels <= readShorts; i += numChannels)
            {
                float mono = 0.0f;
                for (int c = 0; c < numChannels; ++c) mono += raw[i + c] / 32768.0f;
                samples.push_back(mono / numChannels);
            }
        }

        if (!samples.empty())
        {
            float bpm = 120.0f;
            dsp->analyzeFileBuffer(samples, static_cast<float>(sampleRate), bpm);
        }
    }

    void render(HDC hdc)
    {
        RECT rc;
        GetClientRect(hwnd, &rc);
        int w = rc.right - rc.left;
        int h = rc.bottom - rc.top;

        HDC memDC = CreateCompatibleDC(hdc);
        HBITMAP memBitmap = CreateCompatibleBitmap(hdc, w, h);
        HBITMAP oldBitmap = (HBITMAP)SelectObject(memDC, memBitmap);

        Gdiplus::Graphics g(memDC);
        g.SetSmoothingMode(Gdiplus::SmoothingModeAntiAlias);
        g.SetTextRenderingHint(Gdiplus::TextRenderingHintClearTypeGridFit);

        // Background
        Gdiplus::SolidBrush bgBrush(Gdiplus::Color(255, 10, 10, 14));
        g.FillRectangle(&bgBrush, 0, 0, w, h);

        // Header
        Gdiplus::FontFamily fontFamily(L"Segoe UI");
        Gdiplus::Font headerFont(&fontFamily, 11, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::SolidBrush purpleBrush(Gdiplus::Color(255, 138, 43, 226));
        Gdiplus::StringFormat centerFmt;
        centerFmt.SetAlignment(Gdiplus::StringAlignmentCenter);
        centerFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);

        Gdiplus::RectF headerRect(0, 14, (float)w, 20);
        g.DrawString(L"@L8PIEST  |  KEYFINDER VST", -1, &headerFont, headerRect, &centerFmt, &purpleBrush);

        // Live Audio Dot
        bool playing = dsp ? dsp->isAudioPlaying() : false;
        Gdiplus::SolidBrush dotBrush(playing ? Gdiplus::Color(255, 0, 230, 118) : Gdiplus::Color(255, 60, 60, 80));
        g.FillEllipse(&dotBrush, 36, 19, 9, 9);

        // Key Card
        Gdiplus::RectF keyCard(24, 46, (float)w - 48, 150);
        Gdiplus::SolidBrush cardBg(Gdiplus::Color(255, 18, 14, 34));
        Gdiplus::Pen borderPen(Gdiplus::Color(255, 138, 43, 226), 1.8f);
        drawRoundedRect(g, cardBg, borderPen, keyCard, 12.0f);

        // Big Key Display
        auto keyInfo = dsp ? dsp->getLatestKey() : KeyInfo{"READY", "--", 0, 440};
        float bpm = dsp ? dsp->getLatestBpm() : 120.0f;
        bool isSync = dsp ? dsp->isHostSynced() : false;

        std::wstring wKey(keyInfo.keyName.begin(), keyInfo.keyName.end());
        Gdiplus::Font keyFont(&fontFamily, 22, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::SolidBrush whiteBrush(Gdiplus::Color(255, 255, 255, 255));
        Gdiplus::RectF keyTextRect(30, 66, (float)w - 60, 40);
        g.DrawString(wKey.c_str(), -1, &keyFont, keyTextRect, &centerFmt, &whiteBrush);

        // Badges (Camelot, BPM, Tuning)
        float badgeY = 136;
        float bW = 95, bH = 26;
        float startX = ((float)w - (bW * 3 + 20)) / 2;

        // Camelot
        Gdiplus::RectF b1(startX, badgeY, bW, bH);
        Gdiplus::SolidBrush b1Bg(Gdiplus::Color(255, 22, 17, 44));
        Gdiplus::Pen b1Pen(Gdiplus::Color(255, 0, 230, 118), 1.0f);
        drawRoundedRect(g, b1Bg, b1Pen, b1, 6.0f);
        Gdiplus::Font badgeFont(&fontFamily, 11, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::SolidBrush greenBrush(Gdiplus::Color(255, 0, 230, 118));
        std::wstring wCamelot(keyInfo.camelot.begin(), keyInfo.camelot.end());
        g.DrawString(wCamelot.c_str(), -1, &badgeFont, b1, &centerFmt, &greenBrush);

        // BPM
        Gdiplus::RectF b2(startX + bW + 10, badgeY, bW, bH);
        Gdiplus::Pen b2Pen(Gdiplus::Color(255, 176, 102, 254), 1.0f);
        drawRoundedRect(g, b1Bg, b2Pen, b2, 6.0f);
        Gdiplus::SolidBrush violetBrush(Gdiplus::Color(255, 192, 132, 252));
        wchar_t bpmBuf[32];
        swprintf(bpmBuf, 32, L"%.1f BPM", bpm);
        g.DrawString(bpmBuf, -1, &badgeFont, b2, &centerFmt, &violetBrush);

        // Tuning
        Gdiplus::RectF b3(startX + (bW + 10) * 2, badgeY, bW, bH);
        Gdiplus::Pen b3Pen(Gdiplus::Color(255, 60, 45, 95), 1.0f);
        drawRoundedRect(g, b1Bg, b3Pen, b3, 6.0f);
        Gdiplus::SolidBrush grayBrush(Gdiplus::Color(255, 160, 160, 184));
        wchar_t tuneBuf[32];
        swprintf(tuneBuf, 32, L"%.1f Hz", keyInfo.tuningHz);
        g.DrawString(tuneBuf, -1, &badgeFont, b3, &centerFmt, &grayBrush);

        // Note Ranking Card
        Gdiplus::RectF rankCard(24, 210, (float)w - 48, 128);
        Gdiplus::Pen rankPen(Gdiplus::Color(255, 45, 25, 75), 1.0f);
        drawRoundedRect(g, b1Bg, rankPen, rankCard, 10.0f);

        Gdiplus::Font subFont(&fontFamily, 9, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::StringFormat leftFmt;
        leftFmt.SetLineAlignment(Gdiplus::StringAlignmentCenter);
        g.DrawString(L"NOTAS DOMINANTES DETECTADAS", -1, &subFont, Gdiplus::PointF(38, 222), &purpleBrush);

        int maxBars = std::min(4, (int)keyInfo.ranking.size());
        float barY = 246;
        Gdiplus::Font noteFont(&fontFamily, 10, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::Font pctFont(&fontFamily, 9, Gdiplus::FontStyleRegular, Gdiplus::UnitPoint);

        for (int i = 0; i < maxBars; ++i)
        {
            auto item = keyInfo.ranking[i];
            std::wstring nName(item.first.begin(), item.first.end());
            g.DrawString(nName.c_str(), -1, &noteFont, Gdiplus::PointF(38, barY), &whiteBrush);

            float bX = 68;
            float maxBW = (float)w - 160;
            Gdiplus::SolidBrush barSlotBg(Gdiplus::Color(255, 30, 22, 55));
            g.FillRectangle(&barSlotBg, bX, barY + 3, maxBW, 8.0f);

            float fillW = std::clamp((item.second / 35.0f) * maxBW, 4.0f, maxBW);
            Gdiplus::SolidBrush barFill(i == 0 ? Gdiplus::Color(255, 0, 230, 118) : Gdiplus::Color(255, 138, 43, 226));
            g.FillRectangle(&barFill, bX, barY + 3, fillW, 8.0f);

            wchar_t pBuf[16];
            swprintf(pBuf, 16, L"%.1f%%", item.second);
            g.DrawString(pBuf, -1, &pctFont, Gdiplus::PointF((float)w - 82, barY), &grayBrush);

            barY += 18;
        }

        // Drag and Drop Zone
        Gdiplus::RectF dropZone(24, 350, (float)w - 48, 76);
        Gdiplus::Pen dropPen(Gdiplus::Color(255, 138, 43, 226), 1.5f);
        dropPen.SetDashStyle(Gdiplus::DashStyleDash);
        drawRoundedRect(g, cardBg, dropPen, dropZone, 10.0f);

        Gdiplus::Font dropFont(&fontFamily, 10, Gdiplus::FontStyleBold, Gdiplus::UnitPoint);
        Gdiplus::RectF dropTextRect(24, 360, (float)w - 48, 20);
        g.DrawString(L"ARRASTE SAMPLES OU LOOPS DO FL STUDIO AQUI", -1, &dropFont, dropTextRect, &centerFmt, &purpleBrush);

        Gdiplus::Font subDrop(&fontFamily, 9, Gdiplus::FontStyleRegular, Gdiplus::UnitPoint);
        Gdiplus::RectF subTextRect(24, 384, (float)w - 48, 20);
        g.DrawString(L"Ou reproduza o audio no Mixer para analise continua", -1, &subDrop, subTextRect, &centerFmt, &grayBrush);

        // Copy Button
        Gdiplus::RectF btnRect(34, 440, (float)w - 68, 38);
        Gdiplus::SolidBrush btnBg(Gdiplus::Color(255, 45, 11, 90));
        Gdiplus::Pen btnPen(copyFeedbackTimer > 0 ? Gdiplus::Color(255, 0, 230, 118) : Gdiplus::Color(255, 138, 43, 226), 1.2f);
        drawRoundedRect(g, btnBg, btnPen, btnRect, 8.0f);

        const wchar_t* btnText = (copyFeedbackTimer > 0) ? L"COPIADO PARA O FL STUDIO!" : L"COPIAR INFORMACOES";
        g.DrawString(btnText, -1, &headerFont, btnRect, &centerFmt, &whiteBrush);

        // Blit to screen
        BitBlt(hdc, 0, 0, w, h, memDC, 0, 0, SRCCOPY);

        SelectObject(memDC, oldBitmap);
        DeleteObject(memBitmap);
        DeleteDC(memDC);
    }

    void drawRoundedRect(Gdiplus::Graphics& g, Gdiplus::Brush& b, Gdiplus::Pen& p, Gdiplus::RectF r, float radius)
    {
        Gdiplus::GraphicsPath path;
        path.AddArc(r.X, r.Y, radius * 2, radius * 2, 180, 90);
        path.AddArc(r.X + r.Width - radius * 2, r.Y, radius * 2, radius * 2, 270, 90);
        path.AddArc(r.X + r.Width - radius * 2, r.Y + r.Height - radius * 2, radius * 2, radius * 2, 0, 90);
        path.AddArc(r.X, r.Y + r.Height - radius * 2, radius * 2, radius * 2, 90, 90);
        path.CloseFigure();

        g.FillPath(&b, &path);
        g.DrawPath(&p, &path);
    }
};

} // namespace loopiest
