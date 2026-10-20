#include "AuthManager.h"
#include <fstream>
#include <filesystem>
#include <iostream>

namespace loopiest
{

static const int PRIME_WEIGHTS[12] = { 3, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43 };

std::string AuthManager::getVaultLicensePath()
{
    return "C:\\loopiest\\acess\\license.dat";
}

std::string AuthManager::getVaultUserPath()
{
    return "C:\\loopiest\\acess\\user.dat";
}

bool AuthManager::isAuthorized()
{
    // Check if C:\loopiest\acess\license.dat exists and has valid magic or size
    namespace fs = std::filesystem;
    std::string path = getVaultLicensePath();
    if (fs::exists(path))
    {
        auto sz = fs::file_size(path);
        if (sz >= 48) // Encrypted binary format
            return true;
    }
    return false;
}

bool AuthManager::validatePasskey(const std::string& key)
{
    std::regex passkeyRegex("^LPST-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$");
    if (!std::regex_match(key, passkeyRegex))
        return false;

    // Check Block 1
    std::string b1 = key.substr(5, 4);
    int sumB1 = 0;
    for (char c : b1) sumB1 += static_cast<int>(c);
    if (sumB1 % 13 != 5)
        return false;

    // Check Block 2 Parity
    std::string b2 = key.substr(10, 4);
    if ((static_cast<int>(b2[0]) + static_cast<int>(b2[2])) % 2 != 0)
        return false;
    if ((static_cast<int>(b2[1]) + static_cast<int>(b2[3])) % 2 != 1)
        return false;

    // Check Weighted Polynomial Checksum (Blocks 1, 2, 3)
    std::string b3 = key.substr(15, 4);
    std::string s12 = b1 + b2 + b3;
    int weightedTotal = 0;
    for (int i = 0; i < 12; ++i)
        weightedTotal += static_cast<int>(s12[i]) * PRIME_WEIGHTS[i];

    if (weightedTotal % 97 != 42)
        return false;

    return true;
}

bool AuthManager::saveAuthorizedPasskey(const std::string& passkey)
{
    if (!validatePasskey(passkey))
        return false;

    namespace fs = std::filesystem;
    fs::create_directories("C:\\loopiest\\acess");

    // Write authorization marker file
    std::ofstream ofs(getVaultLicensePath(), std::ios::binary);
    if (ofs.is_open())
    {
        // Simple magic header and key
        ofs << "LPST_ENC\x01" << passkey;
        return true;
    }
    return false;
}

std::string AuthManager::getActivePasskey()
{
    return "AUTHORIZED";
}

std::string AuthManager::getProducerHandle()
{
    return "PRODUCER";
}

} // namespace loopiest
