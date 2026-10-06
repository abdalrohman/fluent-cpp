#pragma once

#include "IconsFluentSystem.h"

#include <cstdint>
#include <string>
#include <string_view>
#include <array>
#include <filesystem>

#if defined(__has_include)
  #if __has_include(<imgui.h>)
    #include <imgui.h>
  #elif __has_include("imgui.h")
    #include "imgui.h"
  #endif
#endif

namespace fluent::imgui {

// Types for glyph ranges regardless of whether imgui.h is included
using ImWchar16_t = uint16_t;
using ImWchar32_t = uint32_t;

// 16-bit glyph ranges (0xE000 .. 0xF8FF, 0)
inline constexpr ImWchar16_t GlyphRangesRegular16[] = {
    static_cast<ImWchar16_t>(0xE000),
    static_cast<ImWchar16_t>(0xF8FF),
    static_cast<ImWchar16_t>(0)
};

inline constexpr ImWchar16_t GlyphRangesFilled16[] = {
    static_cast<ImWchar16_t>(0xE000),
    static_cast<ImWchar16_t>(0xF8FF),
    static_cast<ImWchar16_t>(0)
};

// 32-bit glyph ranges (0xE000 .. 0xF8FF, 0xF0000 .. 0xF0CD8 / 0xF0D55, 0)
inline constexpr ImWchar32_t GlyphRangesRegular32[] = {
    static_cast<ImWchar32_t>(0xE000),
    static_cast<ImWchar32_t>(0xF8FF),
    static_cast<ImWchar32_t>(0xF0000),
    static_cast<ImWchar32_t>(0xF0CD8),
    static_cast<ImWchar32_t>(0)
};

inline constexpr ImWchar32_t GlyphRangesFilled32[] = {
    static_cast<ImWchar32_t>(0xE000),
    static_cast<ImWchar32_t>(0xF8FF),
    static_cast<ImWchar32_t>(0xF0000),
    static_cast<ImWchar32_t>(0xF0D55),
    static_cast<ImWchar32_t>(0)
};

// Accessors for static glyph ranges
[[nodiscard]] inline constexpr const ImWchar16_t* GetGlyphRangesRegular16() noexcept {
    return GlyphRangesRegular16;
}

[[nodiscard]] inline constexpr const ImWchar16_t* GetGlyphRangesFilled16() noexcept {
    return GlyphRangesFilled16;
}

[[nodiscard]] inline constexpr const ImWchar32_t* GetGlyphRangesRegular32() noexcept {
    return GlyphRangesRegular32;
}

[[nodiscard]] inline constexpr const ImWchar32_t* GetGlyphRangesFilled32() noexcept {
    return GlyphRangesFilled32;
}

#if defined(IMGUI_VERSION) || defined(ImWchar)
// Automatic range selector based on ImGui's configured ImWchar size
[[nodiscard]] inline const ImWchar* GetGlyphRangesRegular() noexcept {
    if constexpr (sizeof(ImWchar) == sizeof(ImWchar32_t)) {
        return reinterpret_cast<const ImWchar*>(GlyphRangesRegular32);
    } else {
        return reinterpret_cast<const ImWchar*>(GlyphRangesRegular16);
    }
}

[[nodiscard]] inline const ImWchar* GetGlyphRangesFilled() noexcept {
    if constexpr (sizeof(ImWchar) == sizeof(ImWchar32_t)) {
        return reinterpret_cast<const ImWchar*>(GlyphRangesFilled32);
    } else {
        return reinterpret_cast<const ImWchar*>(GlyphRangesFilled16);
    }
}
#endif

// ============================================================================
// UTF-8 Conversion Utilities
// ============================================================================

/**
 * @brief Encodes a 32-bit Unicode codepoint into UTF-8 representation.
 * @param cp Unicode codepoint (e.g. 0xF101 or 0xF0CD8).
 * @param out_buf Buffer of at least 5 bytes to receive null-terminated UTF-8.
 * @return Number of UTF-8 bytes written (excluding null terminator), or 0 on error.
 */
inline int CodepointToUtf8(char32_t cp, char out_buf[5]) noexcept {
    if (!out_buf) return 0;

    if (cp <= 0x7F) {
        out_buf[0] = static_cast<char>(cp);
        out_buf[1] = '\0';
        return 1;
    }
    if (cp <= 0x7FF) {
        out_buf[0] = static_cast<char>(0xC0 | ((cp >> 6) & 0x1F));
        out_buf[1] = static_cast<char>(0x80 | (cp & 0x3F));
        out_buf[2] = '\0';
        return 2;
    }
    if (cp <= 0xFFFF) {
        out_buf[0] = static_cast<char>(0xE0 | ((cp >> 12) & 0x0F));
        out_buf[1] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out_buf[2] = static_cast<char>(0x80 | (cp & 0x3F));
        out_buf[3] = '\0';
        return 3;
    }
    if (cp <= 0x10FFFF) {
        out_buf[0] = static_cast<char>(0xF0 | ((cp >> 18) & 0x07));
        out_buf[1] = static_cast<char>(0x80 | ((cp >> 12) & 0x3F));
        out_buf[2] = static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
        out_buf[3] = static_cast<char>(0x80 | (cp & 0x3F));
        out_buf[4] = '\0';
        return 4;
    }

    out_buf[0] = '\0';
    return 0;
}

/**
 * @brief Encodes a 32-bit Unicode codepoint into a std::string.
 */
inline std::string CodepointToUtf8(char32_t cp) {
    char buf[5] = {0};
    int len = CodepointToUtf8(cp, buf);
    return std::string(buf, static_cast<size_t>(len));
}

/**
 * @brief Decodes the next Unicode codepoint from a UTF-8 string.
 * @param utf8 Pointer to UTF-8 encoded string.
 * @param out_next Optional pointer to receive address immediately after decoded character.
 * @return Decoded char32_t codepoint, or 0 on error / null terminator.
 */
inline char32_t Utf8ToCodepoint(const char* utf8, const char** out_next = nullptr) noexcept {
    if (!utf8 || *utf8 == '\0') {
        if (out_next) *out_next = utf8;
        return 0;
    }

    const auto u = static_cast<unsigned char>(*utf8);
    char32_t cp = 0;
    int bytes = 0;

    if (u < 0x80) {
        cp = u;
        bytes = 1;
    } else if ((u & 0xE0) == 0xC0) {
        cp = u & 0x1F;
        bytes = 2;
    } else if ((u & 0xF0) == 0xE0) {
        cp = u & 0x0F;
        bytes = 3;
    } else if ((u & 0xF8) == 0xF0) {
        cp = u & 0x07;
        bytes = 4;
    } else {
        if (out_next) *out_next = utf8 + 1;
        return 0xFFFD; // Replacement character
    }

    for (int i = 1; i < bytes; ++i) {
        const auto next_u = static_cast<unsigned char>(utf8[i]);
        if ((next_u & 0xC0) != 0x80) {
            if (out_next) *out_next = utf8 + i;
            return 0xFFFD;
        }
        cp = (cp << 6) | (next_u & 0x3F);
    }

    if (out_next) *out_next = utf8 + bytes;
    return cp;
}

// ============================================================================
// Font Path Discovery Helper
// ============================================================================

/**
 * @brief Searches standard asset and project directories for a font file.
 * Checks res/fonts/, ../res/fonts/, third_party/fluent_icons/fonts/, etc.
 * @param font_filename Name of the font file (e.g. "FluentSystemIcons-Regular.ttf").
 * @return Resolved path as std::string, or empty string if not found.
 */
inline std::string FindFontFile(const char* font_filename) {
    if (!font_filename || font_filename[0] == '\0') return {};

    namespace fs = std::filesystem;
    const fs::path candidate_dirs[] = {
        "res/fonts",
        "../res/fonts",
        "../../res/fonts",
        "third_party/fluent_icons/fonts",
        "../third_party/fluent_icons/fonts",
        "../../third_party/fluent_icons/fonts",
        "fonts",
        "../fonts",
        "."
    };

    for (const auto& dir : candidate_dirs) {
        std::error_code ec;
        fs::path p = dir / fs::path(font_filename);
        if (fs::exists(p, ec) && fs::is_regular_file(p, ec)) {
            return p.lexically_normal().string();
        }
    }

    return {};
}

// ============================================================================
// Dear ImGui Font Atlas Helpers
// ============================================================================

#if defined(IMGUI_VERSION)

/**
 * @brief Pre-configured ImFontConfig tailored for merging Fluent Icons into an existing font.
 */
struct FluentFontConfig : public ImFontConfig {
    explicit FluentFontConfig(bool merge = true, float font_size_offset_y = 0.0f) {
        MergeMode = merge;
        PixelSnapH = true;
        OversampleH = 1;
        OversampleV = 1;
        GlyphOffset.y = font_size_offset_y;
    }
};

/**
 * @brief Adds Fluent System Icons Regular to an ImFontAtlas with automatic merge settings.
 */
inline ImFont* AddFluentRegularFont(
    ImFontAtlas* atlas,
    const char* font_path,
    float font_size_pixels,
    const ImFontConfig* custom_config = nullptr,
    const ImWchar* custom_glyph_ranges = nullptr
) {
    if (!atlas || !font_path) return nullptr;

    FluentFontConfig default_config(true);
    const ImFontConfig* cfg = custom_config ? custom_config : &default_config;
    const ImWchar* ranges = custom_glyph_ranges ? custom_glyph_ranges : GetGlyphRangesRegular();

    return atlas->AddFontFromFileTTF(font_path, font_size_pixels, cfg, ranges);
}

/**
 * @brief Adds Fluent System Icons Filled to an ImFontAtlas with automatic merge settings.
 */
inline ImFont* AddFluentFilledFont(
    ImFontAtlas* atlas,
    const char* font_path,
    float font_size_pixels,
    const ImFontConfig* custom_config = nullptr,
    const ImWchar* custom_glyph_ranges = nullptr
) {
    if (!atlas || !font_path) return nullptr;

    FluentFontConfig default_config(true);
    const ImFontConfig* cfg = custom_config ? custom_config : &default_config;
    const ImWchar* ranges = custom_glyph_ranges ? custom_glyph_ranges : GetGlyphRangesFilled();

    return atlas->AddFontFromFileTTF(font_path, font_size_pixels, cfg, ranges);
}

/**
 * @brief Adds Fluent System Icons Regular from memory to an ImFontAtlas.
 */
inline ImFont* AddFluentRegularFontFromMemory(
    ImFontAtlas* atlas,
    void* font_data,
    int font_data_size,
    float font_size_pixels,
    const ImFontConfig* custom_config = nullptr,
    const ImWchar* custom_glyph_ranges = nullptr
) {
    if (!atlas || !font_data || font_data_size <= 0) return nullptr;

    FluentFontConfig default_config(true);
    const ImFontConfig* cfg = custom_config ? custom_config : &default_config;
    const ImWchar* ranges = custom_glyph_ranges ? custom_glyph_ranges : GetGlyphRangesRegular();

    return atlas->AddFontFromMemoryTTF(font_data, font_data_size, font_size_pixels, cfg, ranges);
}

/**
 * @brief Adds Fluent System Icons Filled from memory to an ImFontAtlas.
 */
inline ImFont* AddFluentFilledFontFromMemory(
    ImFontAtlas* atlas,
    void* font_data,
    int font_data_size,
    float font_size_pixels,
    const ImFontConfig* custom_config = nullptr,
    const ImWchar* custom_glyph_ranges = nullptr
) {
    if (!atlas || !font_data || font_data_size <= 0) return nullptr;

    FluentFontConfig default_config(true);
    const ImFontConfig* cfg = custom_config ? custom_config : &default_config;
    const ImWchar* ranges = custom_glyph_ranges ? custom_glyph_ranges : GetGlyphRangesFilled();

    return atlas->AddFontFromMemoryTTF(font_data, font_data_size, font_size_pixels, cfg, ranges);
}

#endif // IMGUI_VERSION

} // namespace fluent::imgui
