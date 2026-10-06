# Fluent UI System Icons for Dear ImGui (C++17 / C++20 / C++23)

[![C++17](https://img.shields.io/badge/C%2B%2B-17%2F20%2F23-blue.svg)](https://en.wikipedia.org/wiki/C%2B%2B17)
[![Dear ImGui](https://img.shields.io/badge/Dear%20ImGui-1.80%2B-orange.svg)](https://github.com/ocornut/imgui)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Fluent Icons Upstream](https://img.shields.io/badge/Microsoft-Fluent%20UI%20System%20Icons-0078D4.svg)](https://github.com/microsoft/fluentui-system-icons)

A standalone, header-only C++ library and font distribution integrating Microsoft's [Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons) into **Dear ImGui**.

Provides both **Regular** and **Filled** icon variants, C-style macros compatible with [IconFontCppHeaders](https://github.com/juliettef/IconFontCppHeaders), modern C++ `std::string_view` / `char32_t` constexpr namespaces, Dear ImGui font atlas helpers, and full support for both 16-bit (`ImWchar`) and 32-bit (`ImWchar32`) glyph ranges.

---

## Table of Contents

- [Features](#features)
- [Directory Structure](#directory-structure)
- [CMake Integration](#cmake-integration)
  - [Method 1: add_subdirectory](#method-1-add_subdirectory)
  - [Method 2: CMake FetchContent](#method-2-cmake-fetchcontent)
  - [Method 3: Manual Header-Only Inclusion](#method-3-manual-header-only-inclusion)
- [Proper Vertical Alignment with Text (`GlyphOffset`)](#proper-vertical-alignment-with-text-glyphoffset)
  - [The Typographic Cause](#the-typographic-cause)
  - [The Solution: `ImFontConfig::GlyphOffset.y`](#the-solution-imfontconfigglyphoffsety)
- [Usage in C++ & Dear ImGui](#usage-in-c--dear-imgui)
  - [1. Macro Syntax (IconFontCppHeaders style)](#1-macro-syntax-iconfontcppheaders-style)
  - [2. Modern C++ Namespaces (std::string_view)](#2-modern-c-namespaces-stdstring_view)
  - [3. Codepoint Constants (char32_t)](#3-codepoint-constants-char32_t)
- [Dear ImGui Font Atlas Configuration](#dear-imgui-font-atlas-configuration)
  - [Merged Icons with Primary Font (Recommended)](#merged-icons-with-primary-font-recommended)
  - [Dedicated Standalone Icon Font](#dedicated-standalone-icon-font)
  - [Automatic Range Selection Helper](#automatic-range-selection-helper)
- [16-bit vs 32-bit Unicode Range Guidance](#16-bit-vs-32-bit-unicode-range-guidance)
- [FreeType Rasterizer Integration & Best Practices](#freetype-rasterizer-integration--best-practices)
- [Helper Utilities in `FluentIcons_ImGui.hpp`](#helper-utilities-in-fluenticons_imguihpp)
- [Regenerating & Updating Icons](#regenerating--updating-icons)
- [License & Attribution](#license--attribution)

---

## Features

- **Comprehensive Icon Set**: Thousands of clean, modern Microsoft Fluent UI System Icons in both **Regular** (outline) and **Filled** styles.
- **Header-Only & Zero Dependencies**: Interface library requiring only standard C++17 (or C++20/C++23) and standard Dear ImGui headers.
- **Dual API Design**:
  - Classic C string literal macros (`ICON_FLR_...` and `ICON_FLF_...`) for seamless string concatenation: `ImGui::Button(ICON_FLR_SEARCH_24 " Search")`.
  - Modern C++ constexpr namespaces (`fluent::regular::...` and `fluent::filled::...`) exposing `std::string_view` and `char32_t` codepoints.
- **Unicode Support**:
  - Standard 16-bit Unicode PUA (`0xE000` .. `0xF8FF`) for default Dear ImGui builds.
  - Full 32-bit Unicode Supplementary PUA-A (`0xF0000` .. `0xF0D55`) when using `IMGUI_USE_WCHAR32`.
- **Pre-packaged Assets**: Pre-extracted TrueType fonts (`FluentSystemIcons-Regular.ttf`, `FluentSystemIcons-Filled.ttf`) and JSON codepoint metadata included directly in the repository.
- **Customization Tooling**: Python 3 generator script included to pull latest icons directly from Microsoft's upstream repository.

---

## Directory Structure

```
fluent_icons/
├── CMakeLists.txt              # CMake target: fluent_icons_imgui (alias: fluent_icons::imgui)
├── LICENSE                     # MIT License (Microsoft Fluent UI Icons + C++ bindings)
├── README.md                   # This documentation
├── fonts/
│   ├── FluentSystemIcons-Regular.ttf   # Regular TrueType font asset
│   ├── FluentSystemIcons-Filled.ttf    # Filled TrueType font asset
│   ├── FluentSystemIcons-Regular.json  # Raw glyph name to codepoint mapping
│   └── FluentSystemIcons-Filled.json   # Raw glyph name to codepoint mapping
├── include/fluent_icons/
│   ├── IconsFluentSystem.h         # Umbrella header (Regular + Filled)
│   ├── IconsFluentSystemRegular.h  # Regular icon macros & C++ namespaces
│   ├── IconsFluentSystemFilled.h   # Filled icon macros & C++ namespaces
│   └── FluentIcons_ImGui.hpp       # Dear ImGui helpers, glyph ranges, & UTF-8 utilities
└── tools/
    └── generate_fluent_icons.py    # Python 3 generator script
```

---

## CMake Integration

### Method 1: `add_subdirectory`

Place `fluent_icons` inside your project (e.g. `third_party/fluent_icons` or `external/fluent_icons`):

```cmake
add_subdirectory(third_party/fluent_icons)

target_link_libraries(my_app PRIVATE fluent_icons::imgui)
```

### Method 2: CMake `FetchContent`

```cmake
include(FetchContent)

FetchContent_Declare(
    fluent_icons
    GIT_REPOSITORY https://github.com/your-org/fluent_icons.git
    GIT_TAG        main
)
FetchContent_MakeAvailable(fluent_icons)

target_link_libraries(my_app PRIVATE fluent_icons::imgui)
```

### Method 3: Manual Header-Only Inclusion

Add `include/` to your target's include directories:

```cmake
target_include_directories(my_app PRIVATE path/to/fluent_icons/include)
```

---

## Proper Vertical Alignment with Text (`GlyphOffset`)

When merging icon fonts into a text font in Dear ImGui using `MergeMode = true`, icons frequently appear **vertically misaligned—sitting higher than uppercase letters**.

```
Unadjusted (Float High):       [Icon] BUTTON TEXT
Properly Adjusted (Aligned):    [Icon] BUTTON TEXT
```

### The Typographic Cause

Understanding why this occurs comes down to font em-box metrics:

```
+------------------------------------+  <-- Top of Em-Square / Icon Top (100%)
|         .---.                      |
|        /     \   [ICON GLYPH]      |
|        \     /                     |
|  .---.  `---'    +---------------+ |  <-- Cap-Height (~71%): Top of 'B', 'T', 'X'
|  |   |           | |             | |
|  |---|   TEXT    | |             | |  <-- x-Height (~52%): Top of 'x', 'a', 'e'
|  |   |  GLYPHS   | |             | |
+--+---+-----------+-+-------------+-+  <-- BASELINE (0%)
|                  | |               |
|                  '-'               |  <-- Descender (~ -24%): Bottom of 'g', 'p', 'y'
+------------------------------------+  <-- Bottom of Em-Square
```

1. **Standard Text Fonts** (e.g., *Inter*, *Roboto*, *Source Sans Pro*, *Segoe UI*) reserve approximately **$24\%$ of their vertical em-height below the baseline** for lowercase descenders (such as 'g', 'j', 'p', 'q', 'y'). As a result, the **Cap-Height** (top of uppercase letters 'A'–'Z') only reaches approximately **$70\%\text{--}73\%$** of the em-box above the baseline.
2. **Icon Fonts** (such as *Fluent UI System Icons*) have no lowercase descenders. Glyphs are drawn inside a square bounding box designed to occupy the full em-height ($0\%\text{--}100\%$) sitting directly on or above the baseline.
3. **The Conflict**: When merged at the baseline, the icon's top extends to $100\%$ of the em-height, whereas the adjacent capital letters reach only $\approx 71\%$. Visually, the icon appears to "float" above the text line.

### The Solution: `ImFontConfig::GlyphOffset.y`

Dear ImGui's `ImFontConfig` provides `GlyphOffset` to shift the rasterized glyphs during atlas generation without affecting line metrics or text baseline calculation.

To align the visual optical center of Fluent Icons with capital letters:
- For standard UI font sizes ($14\text{px}\text{--}16\text{px}$), set `iconConfig.GlyphOffset.y = 1.5f;`.
- For dynamic/DPI-scaled sizes, set `iconConfig.GlyphOffset.y = std::round(fontSize * 0.10f);` (offsetting by $\approx 10\%$ of the font size).

```cpp
#include <fluent_icons/IconsFluentSystem.h>
#include <fluent_icons/FluentIcons_ImGui.hpp>
#include <imgui.h>
#include <cmath>

ImGuiIO& io = ImGui::GetIO();
const float fontSize = 16.0f;

// 1. Primary Text Font
ImFontConfig textConfig;
ImFont* mainFont = io.Fonts->AddFontFromFileTTF("fonts/Inter-Regular.ttf", fontSize, &textConfig);

// 2. Merged Fluent Icons with GlyphOffset
ImFontConfig iconConfig;
iconConfig.MergeMode  = true;
iconConfig.PixelSnapH = true;

// Shift icons downward to align with text cap-height:
iconConfig.GlyphOffset.y = std::round(fontSize * 0.10f); // e.g. 1.5f or 2.0f

const ImWchar* iconRanges = fluent::imgui::GetGlyphRangesRegular();
io.Fonts->AddFontFromFileTTF("fonts/FluentSystemIcons-Regular.ttf", fontSize, &iconConfig, iconRanges);

io.Fonts->Build();
```

---

## Usage in C++ & Dear ImGui

### 1. Macro Syntax (IconFontCppHeaders style)

C preprocessor string literal macros allow seamless string concatenation with zero runtime overhead:

```cpp
#include <fluent_icons/IconsFluentSystem.h>
#include <imgui.h>

// Buttons with merged icons
ImGui::Button(ICON_FLR_SEARCH_24 " Search");
ImGui::Button(ICON_FLR_SAVE_24 " Save Project");
ImGui::Button(ICON_FLR_DISMISS_24 " Cancel");

// Filled icons
ImGui::Text(ICON_FLF_CHECKMARK_CIRCLE_24 " Operation successful!");
ImGui::TextColored(ImVec4(1.0f, 0.3f, 0.3f, 1.0f), ICON_FLF_ERROR_CIRCLE_24 " Critical Error");
```

### 2. Modern C++ Namespaces (`std::string_view`)

Type-safe, modern C++ `std::string_view` constants are available under `fluent::regular` and `fluent::filled`:

```cpp
#include <fluent_icons/IconsFluentSystem.h>
#include <imgui.h>
#include <string>

namespace flr = fluent::regular;
namespace flf = fluent::filled;

// Use directly in format strings or std::string construction:
ImGui::Button((std::string(flr::arrow_download_24) + " Download Update").c_str());
ImGui::Text("%s Logged in as Administrator", flf::person_24.data());
```

### 3. Codepoint Constants (`char32_t`)

Raw Unicode codepoints are defined as `constexpr char32_t` in `fluent::codepoints`:

```cpp
#include <fluent_icons/IconsFluentSystem.h>

constexpr char32_t search_cp   = fluent::codepoints::regular::search_24;
constexpr char32_t settings_cp = fluent::codepoints::filled::settings_24;
```

---

## Dear ImGui Font Atlas Configuration

### Merged Icons with Primary Font (Recommended)

Merging icons into your primary UI font creates a single unified `ImFont*` pointer:

```cpp
#include <fluent_icons/FluentIcons_ImGui.hpp>
#include <imgui.h>
#include <cmath>

ImGuiIO& io = ImGui::GetIO();
float uiFontSize = 16.0f;

// 1. Load primary font
ImFont* uiFont = io.Fonts->AddFontFromFileTTF("fonts/Inter-Regular.ttf", uiFontSize);

// 2. Merge Fluent Regular Icons
ImFontConfig iconConfig;
iconConfig.MergeMode     = true;
iconConfig.PixelSnapH    = true;
iconConfig.GlyphOffset.y = std::round(uiFontSize * 0.10f); // Vertical alignment fix

io.Fonts->AddFontFromFileTTF(
    "fonts/FluentSystemIcons-Regular.ttf",
    uiFontSize,
    &iconConfig,
    fluent::imgui::GetGlyphRangesRegular()
);

io.Fonts->Build();
```

### Dedicated Standalone Icon Font

If you need large standalone icons (e.g., for toolbar buttons or dedicated icon pickers) without merging into text:

```cpp
ImFontConfig dedicatedConfig;
dedicatedConfig.MergeMode = false;
dedicatedConfig.PixelSnapH = true;

ImFont* largeIconsFont = io.Fonts->AddFontFromFileTTF(
    "fonts/FluentSystemIcons-Filled.ttf",
    28.0f,
    &dedicatedConfig,
    fluent::imgui::GetGlyphRangesFilled()
);
```

Then switch fonts in your ImGui render loop:

```cpp
ImGui::PushFont(largeIconsFont);
ImGui::Text(ICON_FLF_FOLDER_OPEN_24);
ImGui::PopFont();
```

### Automatic Range Selection Helper

`FluentIcons_ImGui.hpp` provides `GetGlyphRangesRegular()` and `GetGlyphRangesFilled()` which automatically query `sizeof(ImWchar)` at compile time and return the appropriate 16-bit or 32-bit glyph range array.

---

## 16-bit vs 32-bit Unicode Range Guidance

Fluent UI System Icons are assigned codepoints in the Unicode Private Use Areas:

| Range Identifier | Codepoint Interval | Supported by Default ImGui? | Notes |
|---|---|---|---|
| **16-bit Basic Multilingual Plane (BMP) PUA** | `0xE000` .. `0xF8FF` | **Yes** (`ImWchar` = `uint16_t`) | Contains several thousand core icons across sizes 16, 20, 24, 28, 32, 48. |
| **32-bit Supplementary PUA-A** | `0xF0000` .. `0xF0D55` | Requires `IMGUI_USE_WCHAR32` | Contains extended high-codepoint variants and newest icon additions. |

### Enabling 32-bit Glyphs in Dear ImGui

If you need icons located in the Supplementary Private Use Area (`0xF0000+`), define `IMGUI_USE_WCHAR32` in your build configuration:

In CMake:
```cmake
target_compile_definitions(my_app PRIVATE IMGUI_USE_WCHAR32)
```

Or in `imconfig.h`:
```cpp
#define IMGUI_USE_WCHAR32
```

---

## FreeType Rasterizer Integration & Best Practices

When building Dear ImGui with FreeType (`imgui_freetype` / `ImGuiFreeType`):

1. **Disable Oversampling**: FreeType performs its own subpixel hinting. Set `OversampleH = 0` and `OversampleV = 0` (or `1`) to avoid unnecessary rasterizer blurs and reduce texture atlas memory footprint.
2. **Pixel Snapping**: Set `PixelSnapH = false` when using FreeType (FreeType's hinting already handles subpixel positioning).

```cpp
#include "imgui_freetype.h"
#include <fluent_icons/FluentIcons_ImGui.hpp>

ImGuiIO& io = ImGui::GetIO();
io.Fonts->SetFontLoader(ImGuiFreeType::GetFontLoader());

ImFontConfig fontCfg;
fontCfg.OversampleH = 0;
fontCfg.OversampleV = 0;
fontCfg.PixelSnapH  = false;
fontCfg.RasterizerMultiply = 1.0f;

ImFont* mainFont = io.Fonts->AddFontFromFileTTF("fonts/Inter-Regular.ttf", 16.0f, &fontCfg);

ImFontConfig iconCfg;
iconCfg.MergeMode          = true;
iconCfg.OversampleH        = 0;
iconCfg.OversampleV        = 0;
iconCfg.PixelSnapH         = false;
iconCfg.RasterizerMultiply = 1.0f;
iconCfg.GlyphOffset.y      = 1.5f; // Vertical alignment fix

io.Fonts->AddFontFromFileTTF(
    "fonts/FluentSystemIcons-Regular.ttf",
    16.0f,
    &iconCfg,
    fluent::imgui::GetGlyphRangesRegular()
);

io.Fonts->Build();
```

---

## Helper Utilities in `FluentIcons_ImGui.hpp`

The header `<fluent_icons/FluentIcons_ImGui.hpp>` includes convenience helpers:

- **`fluent::imgui::FluentFontConfig`**: Pre-configured `ImFontConfig` struct with optional Y offset parameter:
  ```cpp
  fluent::imgui::FluentFontConfig iconCfg(true /* merge */, 1.5f /* offset y */);
  ```
- **`fluent::imgui::AddFluentRegularFont(...)`**: One-line font registration helper:
  ```cpp
  ImFont* font = fluent::imgui::AddFluentRegularFont(io.Fonts, "fonts/FluentSystemIcons-Regular.ttf", 16.0f);
  ```
- **`fluent::imgui::CodepointToUtf8(char32_t cp)`**: Encodes any 32-bit Unicode codepoint into a standard UTF-8 string.
- **`fluent::imgui::Utf8ToCodepoint(const char* utf8)`**: Decodes the first Unicode character from a UTF-8 string.
- **`fluent::imgui::FindFontFile(const char* filename)`**: Resolves font paths across standard asset folders (`res/fonts/`, `fonts/`, etc.).

---

## Regenerating & Updating Icons

To update icons to the latest upstream release from Microsoft:

```bash
python3 tools/generate_fluent_icons.py
```

### Generator Command-Line Options

| Flag | Default | Description |
|---|---|---|
| `--output-dir <path>` | `include/fluent_icons` | Target directory for generated C++ headers |
| `--fonts-dir <path>` | `fonts` | Target directory for downloaded TTF and JSON files |
| `--res-fonts-dir <path>` | `None` | Optional external project assets/fonts directory to sync TTF files |
| `--force-download` | `false` | Force re-downloading files even if present locally |
| `--no-download` | `false` | Skip download and regenerate headers from local files |

---

## License & Attribution

- **Fluent UI System Icons Font Assets**: Copyright (c) 2020-2026 **Microsoft Corporation**.
  Licensed under the [MIT License](LICENSE).
- **C++ Headers, CMake Bindings, and Utilities**: Copyright (c) 2026 **Fluent Icons for ImGui Contributors**.
  Licensed under the [MIT License](LICENSE).
