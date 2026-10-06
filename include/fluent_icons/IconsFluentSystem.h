// Umbrella header for Microsoft Fluent UI System Icons (Regular & Filled)
// Compatible with Dear ImGui and IconFontCppHeaders
#pragma once

#include "IconsFluentSystemRegular.h"
#include "IconsFluentSystemFilled.h"

#if defined(__cplusplus)
namespace fluent {
    namespace reg = regular;
    namespace fill = filled;

    namespace cp {
        namespace reg = codepoints::regular;
        namespace fill = codepoints::filled;
    }
} // namespace fluent
#endif // __cplusplus
