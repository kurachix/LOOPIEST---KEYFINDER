#include <windows.h>
#include <cstdint>
#include <cstring>
#include <memory>
#include "VstDsp.h"
#include "VstGui.h"

#define VST_MAGIC 0x56737450 // 'VstP'

#pragma pack(push, 8)
struct ERect
{
    int16_t top;
    int16_t left;
    int16_t bottom;
    int16_t right;
};

struct AEffect;
typedef intptr_t (*audioMasterCallback)(struct AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
typedef intptr_t (*AEffectDispatcherProc)(struct AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
typedef void (*AEffectProcessProc)(struct AEffect* effect, float** inputs, float** outputs, int32_t sampleframes);
typedef void (*AEffectSetParameterProc)(struct AEffect* effect, int32_t index, float parameter);
typedef float (*AEffectGetParameterProc)(struct AEffect* effect, int32_t index);

struct VstTimeInfo
{
    double samplePos;
    double sampleRate;
    double nanoSeconds;
    double ppqPos;
    double tempo;
    double bars;
    double cycleStartPos;
    double cycleEndPos;
    int32_t timeSigNumerator;
    int32_t timeSigDenominator;
    int32_t smpteOffset;
    int32_t smpteFrameRate;
    int32_t samplesToNextClock;
    int32_t flags;
};

struct AEffect
{
    int32_t magic;
    AEffectDispatcherProc dispatcher;
    AEffectProcessProc process;
    AEffectSetParameterProc setParameter;
    AEffectGetParameterProc getParameter;
    int32_t numPrograms;
    int32_t numParams;
    int32_t numInputs;
    int32_t numOutputs;
    int32_t flags;
    intptr_t resvd1;
    intptr_t resvd2;
    int32_t initialDelay;
    int32_t realQualities;
    int32_t offQualities;
    float ioRatio;
    void* user;
    void* ptr2;
    AEffectProcessProc processReplacing;
    void* processDoubleReplacing;
    char future[56];
};
#pragma pack(pop)

class LoopiestVstInstance
{
public:
    LoopiestVstInstance(audioMasterCallback master)
        : audioMaster(master), sampleRate(44100.0f), blockSize(512)
    {
        dsp = std::make_unique<loopiest::VstDsp>();
        gui = std::make_unique<loopiest::VstGui>(dsp.get());

        rect.top = 0;
        rect.left = 0;
        rect.bottom = 500;
        rect.right = 460;
    }

    ~LoopiestVstInstance()
    {
        if (gui) gui->close();
    }

    audioMasterCallback audioMaster;
    std::unique_ptr<loopiest::VstDsp> dsp;
    std::unique_ptr<loopiest::VstGui> gui;
    ERect rect;
    float sampleRate;
    int blockSize;
};

#define VSTCALLBACK

static intptr_t Dispatcher(AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt)
{
    LoopiestVstInstance* inst = (LoopiestVstInstance*)effect->user;

    switch (opcode)
    {
        case 0: // effOpen
            return 0;

        case 1: // effClose
            delete inst;
            delete effect;
            return 0;

        case 10: // effSetSampleRate
            if (inst) inst->sampleRate = opt;
            return 0;

        case 11: // effSetBlockSize
            if (inst) inst->blockSize = (int)value;
            return 0;

        case 13: // effEditGetRect
            if (inst && ptr)
            {
                *(ERect**)ptr = &inst->rect;
                return 1;
            }
            return 0;

        case 14: // effEditOpen
            if (inst && inst->gui)
            {
                return inst->gui->open(ptr) ? 1 : 0;
            }
            return 0;

        case 15: // effEditClose
            if (inst && inst->gui)
            {
                inst->gui->close();
                return 1;
            }
            return 0;

        case 19: // effEditIdle
            return 0;

        case 45: // effGetEffectName
            if (ptr) { strncpy((char*)ptr, "LOOPIEST KEYFINDER", 32); return 1; }
            return 0;

        case 47: // effGetVendorString
            if (ptr) { strncpy((char*)ptr, "LOOPIEST", 32); return 1; }
            return 0;

        case 48: // effGetProductString
            if (ptr) { strncpy((char*)ptr, "LOOPIEST KEYFINDER", 32); return 1; }
            return 0;

        case 49: // effGetVendorVersion
            return 1000;

        case 35: // effGetPlugCategory
            return 1; // kPlugCategEffect

        case 51: // effCanDo
            if (ptr)
            {
                if (strcmp((char*)ptr, "receiveVstTimeInfo") == 0) return 1;
                if (strcmp((char*)ptr, "hasCockosExtensions") == 0) return 0;
            }
            return 0;
    }
    return 0;
}

static void ProcessReplacing(AEffect* effect, float** inputs, float** outputs, int32_t sampleframes)
{
    LoopiestVstInstance* inst = (LoopiestVstInstance*)effect->user;
    if (!inst) return;

    // Pass-through audio so audio plays cleanly in FL Studio Mixer
    for (int ch = 0; ch < 2; ++ch)
    {
        if (inputs[ch] && outputs[ch])
        {
            if (inputs[ch] != outputs[ch])
                memcpy(outputs[ch], inputs[ch], sampleframes * sizeof(float));
        }
    }

    // Retrieve host BPM from FL Studio transport
    float hostBpm = 0.0f;
    if (inst->audioMaster)
    {
        VstTimeInfo* timeInfo = (VstTimeInfo*)inst->audioMaster(effect, 7 /* audioMasterGetTime */, 0, 1 /* kVstTempoValid */, NULL, 0.0f);
        if (timeInfo && (timeInfo->flags & 1) && timeInfo->tempo > 30.0 && timeInfo->tempo < 350.0)
        {
            hostBpm = (float)timeInfo->tempo;
        }
    }

    // Process DSP
    const float* left = inputs[0];
    const float* right = (inputs[1] ? inputs[1] : inputs[0]);
    inst->dsp->processSamples(left, right, sampleframes, inst->sampleRate, hostBpm);
}

// ==============================================================================
// VST2 Entry Point
// ==============================================================================
extern "C" __declspec(dllexport) AEffect* VSTPluginMain(audioMasterCallback audioMaster)
{
    AEffect* effect = new AEffect();
    memset(effect, 0, sizeof(AEffect));

    LoopiestVstInstance* instance = new LoopiestVstInstance(audioMaster);

    effect->magic = VST_MAGIC;
    effect->dispatcher = Dispatcher;
    effect->process = nullptr;
    effect->processReplacing = ProcessReplacing;
    effect->setParameter = [](AEffect*, int32_t, float) {};
    effect->getParameter = [](AEffect*, int32_t) { return 0.0f; };
    effect->numPrograms = 1;
    effect->numParams = 0;
    effect->numInputs = 2;
    effect->numOutputs = 2;
    effect->flags = (1 << 0) /* effFlagsHasEditor */ | (1 << 4) /* effFlagsCanReplacing */;
    effect->user = instance;

    return effect;
}

// ==============================================================================
// VST3 Entry Point (GetPluginFactory)
// ==============================================================================
extern "C" __declspec(dllexport) bool InitDll() { return true; }
extern "C" __declspec(dllexport) bool ExitDll() { return true; }

// Minimal VST3 factory stub conforming to Steinberg VST3 binary layout
struct FUnknown;
struct IPluginFactory
{
    virtual int32_t queryInterface(const char* iid, void** obj) = 0;
    virtual uint32_t addRef() = 0;
    virtual uint32_t release() = 0;
    virtual int32_t getFactoryInfo(void* info) = 0;
    virtual int32_t countClasses() = 0;
    virtual int32_t getClassInfo(int32_t index, void* info) = 0;
    virtual int32_t createInstance(const char* cid, const char* _iid, void** obj) = 0;
};

class DummyFactory : public IPluginFactory
{
public:
    int32_t queryInterface(const char*, void**) override { return 0; }
    uint32_t addRef() override { return 1; }
    uint32_t release() override { return 1; }
    int32_t getFactoryInfo(void*) override { return 0; }
    int32_t countClasses() override { return 1; }
    int32_t getClassInfo(int32_t, void*) override { return 0; }
    int32_t createInstance(const char*, const char*, void**) override { return 0; }
};

static DummyFactory gFactory;

extern "C" __declspec(dllexport) void* GetPluginFactory()
{
    return &gFactory;
}

BOOL WINAPI DllMain(HINSTANCE, DWORD, LPVOID)
{
    return TRUE;
}
