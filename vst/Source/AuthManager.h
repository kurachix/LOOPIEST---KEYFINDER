#pragma once

#include <string>
#include <vector>
#include <regex>

namespace loopiest
{

class AuthManager
{
public:
    static bool isAuthorized();
    static bool validatePasskey(const std::string& passkey);
    static bool saveAuthorizedPasskey(const std::string& passkey);
    static std::string getActivePasskey();
    static std::string getProducerHandle();

private:
    static std::string getVaultLicensePath();
    static std::string getVaultUserPath();
};

} // namespace loopiest
