#!/usr/bin/env python3
"""
generate_fluent_icons.py - Standalone Fluent UI System Icons Generator for Dear ImGui.

Downloads FluentSystemIcons-Regular.ttf and FluentSystemIcons-Filled.ttf (and metadata)
from microsoft/fluentui-system-icons, parses font cmap/post tables or JSON metadata,
and generates IconFontCppHeaders-compatible C/C++ headers and modern C++ namespaces.

Dependencies: Python 3 standard library only.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import struct
import sys
import time
import urllib.request
from typing import Dict, List, Optional, Tuple

# =============================================================================
# Configuration & Mirrors
# =============================================================================

MIRRORS = [
    # Primary: GitHub Raw main branch
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/fonts/",
    # Mirror 1: jsDelivr CDN
    "https://cdn.jsdelivr.net/gh/microsoft/fluentui-system-icons@main/fonts/",
    # Mirror 2: GitHub Raw master branch
    "https://raw.githubusercontent.com/microsoft/fluentui-system-icons/master/fonts/",
]

FONTS = {
    "regular": {
        "ttf": "FluentSystemIcons-Regular.ttf",
        "json": "FluentSystemIcons-Regular.json",
        "prefix_macro": "ICON_FLR_",
        "min_macro": "ICON_MIN_FLR",
        "max_16_macro": "ICON_MAX_16_FLR",
        "max_macro": "ICON_MAX_FLR",
        "file_macro": "FONT_ICON_FILE_NAME_FLR",
        "ns": "regular",
        "header": "IconsFluentSystemRegular.h",
        "suffix": "_regular",
    },
    "filled": {
        "ttf": "FluentSystemIcons-Filled.ttf",
        "json": "FluentSystemIcons-Filled.json",
        "prefix_macro": "ICON_FLF_",
        "min_macro": "ICON_MIN_FLF",
        "max_16_macro": "ICON_MAX_16_FLF",
        "max_macro": "ICON_MAX_FLF",
        "file_macro": "FONT_ICON_FILE_NAME_FLF",
        "ns": "filled",
        "header": "IconsFluentSystemFilled.h",
        "suffix": "_filled",
    },
}

# =============================================================================
# Download Utility with Progress & SHA256 Verification
# =============================================================================

def download_file(filename: str, dest_path: str, mirrors: List[str], force: bool = False, retries: int = 3) -> bool:
    """Downloads a file from mirrors with streaming progress and hash calculation."""
    if os.path.exists(dest_path) and not force and os.path.getsize(dest_path) > 0:
        print(f"  [OK] Using existing file: {dest_path} ({os.path.getsize(dest_path)} bytes)")
        return True

    os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
    temp_path = dest_path + ".tmp"

    for mirror in mirrors:
        url = mirror + filename
        for attempt in range(1, retries + 1):
            try:
                print(f"  [>] Fetching {filename} from {url} (attempt {attempt}/{retries})...")
                req = urllib.request.Request(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; FluentIconsGenerator/1.0)",
                        "Accept": "*/*",
                    }
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    total_size = int(resp.headers.get("Content-Length", 0))
                    downloaded = 0
                    hasher = hashlib.sha256()
                    start_time = time.time()

                    with open(temp_path, "wb") as out_f:
                        while True:
                            chunk = resp.read(65536)
                            if not chunk:
                                break
                            out_f.write(chunk)
                            hasher.update(chunk)
                            downloaded += len(chunk)

                            # Progress report
                            if total_size > 0:
                                percent = (downloaded / total_size) * 100.0
                                sys.stdout.write(f"\r      Downloaded {downloaded}/{total_size} bytes ({percent:.1f}%)")
                            else:
                                sys.stdout.write(f"\r      Downloaded {downloaded} bytes")
                            sys.stdout.flush()

                    elapsed = max(0.001, time.time() - start_time)
                    sys.stdout.write(f"\r      Downloaded {downloaded} bytes in {elapsed:.2f}s ({downloaded / elapsed / 1024:.1f} KB/s)\n")
                    sys.stdout.flush()

                    sha256 = hasher.hexdigest()
                    print(f"      SHA-256: {sha256}")

                    if total_size > 0 and downloaded < total_size:
                        raise IOError(f"Truncated download: got {downloaded}, expected {total_size}")

                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.rename(temp_path, dest_path)
                    print(f"  [OK] Saved {dest_path}")
                    return True

            except Exception as e:
                print(f"      [WARN] Failed to download {url}: {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                time.sleep(1)

    print(f"  [ERROR] All mirrors failed for {filename}")
    return False

# =============================================================================
# TTF File Parsing (Standard library struct)
# =============================================================================

def parse_ttf_tables(ttf_path: str) -> Tuple[Dict[int, int], Dict[int, str]]:
    """
    Parses TrueType Font file cmap (formats 4 and 12) and post (format 2.0) tables.
    Returns: (char_to_glyph_map, glyph_to_name_map)
    """
    with open(ttf_path, "rb") as f:
        data = f.read()

    if len(data) < 12:
        return {}, {}

    sfnt_version, num_tables = struct.unpack(">4sH", data[:6])
    tables = {}
    for i in range(num_tables):
        offset = 12 + i * 16
        if offset + 16 > len(data):
            break
        tag, check_sum, table_offset, length = struct.unpack(">4sIII", data[offset:offset+16])
        tag_str = tag.decode("latin1", errors="replace")
        tables[tag_str] = (table_offset, length)

    # 1. Parse cmap table
    char_to_glyph: Dict[int, int] = {}
    if "cmap" in tables:
        cmap_offset, _ = tables["cmap"]
        version, num_subtables = struct.unpack(">HH", data[cmap_offset:cmap_offset+4])
        for i in range(num_subtables):
            sub_entry = cmap_offset + 4 + i * 8
            if sub_entry + 8 > len(data):
                break
            plat_id, enc_id, sub_offset = struct.unpack(">HHI", data[sub_entry:sub_entry+8])
            target_offset = cmap_offset + sub_offset
            if target_offset + 2 > len(data):
                continue
            fmt = struct.unpack(">H", data[target_offset:target_offset+2])[0]

            if fmt == 4:
                # Format 4 (16-bit mappings)
                f4 = data[target_offset:]
                if len(f4) >= 14:
                    length, language, seg_count_x2 = struct.unpack(">HHH", f4[2:8])
                    seg_count = seg_count_x2 // 2
                    if len(f4) >= 16 + seg_count * 8:
                        end_codes = struct.unpack(f">{seg_count}H", f4[14:14+seg_count*2])
                        start_offset = 16 + seg_count * 2
                        start_codes = struct.unpack(f">{seg_count}H", f4[start_offset:start_offset+seg_count*2])
                        delta_offset = start_offset + seg_count * 2
                        id_deltas = struct.unpack(f">{seg_count}h", f4[delta_offset:delta_offset+seg_count*2])
                        ro_offset = delta_offset + seg_count * 2
                        id_range_offsets = struct.unpack(f">{seg_count}H", f4[ro_offset:ro_offset+seg_count*2])

                        for s in range(seg_count - 1):
                            start = start_codes[s]
                            end = end_codes[s]
                            delta = id_deltas[s]
                            ro = id_range_offsets[s]
                            for cp in range(start, end + 1):
                                if ro == 0:
                                    gid = (cp + delta) & 0xFFFF
                                else:
                                    ro_addr = ro_offset + s * 2 + ro
                                    glyph_idx_addr = ro_addr + 2 * (cp - start)
                                    if glyph_idx_addr + 2 <= len(f4):
                                        gid = struct.unpack(">H", f4[glyph_idx_addr:glyph_idx_addr+2])[0]
                                        if gid != 0:
                                            gid = (gid + delta) & 0xFFFF
                                    else:
                                        gid = 0
                                if gid != 0:
                                    char_to_glyph[cp] = gid

            elif fmt == 12:
                # Format 12 (32-bit segmented coverage)
                f12 = data[target_offset:]
                if len(f12) >= 16:
                    _, _, length, lang, num_groups = struct.unpack(">HHIII", f12[:16])
                    if len(f12) >= 16 + num_groups * 12:
                        for g in range(num_groups):
                            start_char, end_char, start_gid = struct.unpack(">III", f12[16+g*12:28+g*12])
                            for cp in range(start_char, end_char + 1):
                                gid = start_gid + (cp - start_char)
                                char_to_glyph[cp] = gid

    # 2. Parse post table (format 2.0 glyph names)
    glyph_to_name: Dict[int, str] = {}
    if "post" in tables:
        post_offset, post_length = tables["post"]
        if post_offset + 34 <= len(data):
            v_maj, v_min = struct.unpack(">HH", data[post_offset:post_offset+4])
            if v_maj == 2:
                num_glyphs = struct.unpack(">H", data[post_offset+32:post_offset+34])[0]
                if post_offset + 34 + num_glyphs * 2 <= len(data):
                    glyph_name_indices = struct.unpack(
                        f">{num_glyphs}H",
                        data[post_offset+34:post_offset+34+num_glyphs*2]
                    )
                    str_table_offset = post_offset + 34 + num_glyphs * 2
                    curr = str_table_offset
                    custom_names: List[str] = []
                    while curr < post_offset + post_length and curr < len(data):
                        str_len = data[curr]
                        curr += 1
                        if curr + str_len <= len(data):
                            name = data[curr:curr+str_len].decode("latin1", errors="replace")
                            curr += str_len
                            custom_names.append(name)
                        else:
                            break

                    for gid, idx in enumerate(glyph_name_indices):
                        if idx >= 258:
                            c_idx = idx - 258
                            if c_idx < len(custom_names):
                                glyph_to_name[gid] = custom_names[c_idx]

    return char_to_glyph, glyph_to_name

# =============================================================================
# Name Normalization & Codepoint Formatting
# =============================================================================

def clean_icon_name(raw_name: str, suffix: str) -> str:
    """
    Normalizes an icon name like 'ic_fluent_access_time_24_regular' -> 'access_time_24'.
    """
    clean = raw_name
    if clean.startswith("ic_fluent_"):
        clean = clean[len("ic_fluent_"):]
    if clean.endswith(suffix):
        clean = clean[:-len(suffix)]
    clean = clean.strip("_")
    # Replace non-alphanumerics with underscore
    clean = re.sub(r"[^a-zA-Z0-9_]", "_", clean).lower()
    return clean

def to_c_utf8_literal(cp: int) -> str:
    """Encodes a Unicode codepoint as a C/C++ string literal (e.g. '\\xef\\x84\\x81')."""
    u8_bytes = chr(cp).encode("utf-8")
    return "".join(f"\\x{b:02x}" for b in u8_bytes)

# =============================================================================
# Header Generation
# =============================================================================

def generate_variant_header(
    font_key: str,
    icons_data: Dict[str, int],
    output_path: str
) -> None:
    """Generates IconsFluentSystemRegular.h or IconsFluentSystemFilled.h."""
    cfg = FONTS[font_key]
    suffix = cfg["suffix"]
    prefix = cfg["prefix_macro"]
    file_name = cfg["ttf"]

    # Process and sort icons
    items = []
    for raw_name, cp in icons_data.items():
        ident = clean_icon_name(raw_name, suffix)
        if not ident:
            continue
        macro_name = f"{prefix}{ident.upper()}"
        utf8_str = to_c_utf8_literal(cp)
        items.append((ident, macro_name, cp, utf8_str))

    # Sort deterministically by identifier
    items.sort(key=lambda x: x[0])

    if not items:
        raise ValueError(f"No icons found for {font_key}")

    all_cps = [x[2] for x in items]
    min_cp = min(all_cps)
    max_16_cp = max(cp for cp in all_cps if cp <= 0xFFFF)
    max_cp = max(all_cps)

    lines = []
    lines.append("// Generated by generate_fluent_icons.py")
    lines.append("// Based on Microsoft Fluent UI System Icons (MIT License)")
    lines.append("// https://github.com/microsoft/fluentui-system-icons")
    lines.append("//")
    lines.append("// Compatible with IconFontCppHeaders and modern C++ (C++17/20/23)")
    lines.append("#pragma once")
    lines.append("")
    lines.append(f'#define {cfg["file_macro"]} "{file_name}"')
    lines.append("")
    lines.append(f'#define {cfg["min_macro"]} 0x{min_cp:x}')
    lines.append(f'#define {cfg["max_16_macro"]} 0x{max_16_cp:x}')
    lines.append(f'#define {cfg["max_macro"]} 0x{max_cp:x}')
    lines.append("")
    lines.append("// C-style string literal macros (IconFontCppHeaders format)")

    for ident, macro_name, cp, utf8_str in items:
        lines.append(f'#define {macro_name} "{utf8_str}"\t// U+{cp:04X} ({cp})')

    lines.append("")
    lines.append("#if defined(__cplusplus)")
    lines.append("#include <string_view>")
    lines.append("#include <cstdint>")
    lines.append("")
    lines.append(f"namespace fluent::{cfg['ns']} {{")
    lines.append("")
    for ident, macro_name, cp, utf8_str in items:
        lines.append(f'    inline constexpr std::string_view {ident} = {macro_name};')
    lines.append("")
    lines.append(f"}} // namespace fluent::{cfg['ns']}")
    lines.append("")
    lines.append(f"namespace fluent::codepoints::{cfg['ns']} {{")
    lines.append("")
    for ident, macro_name, cp, utf8_str in items:
        lines.append(f'    inline constexpr char32_t {ident} = 0x{cp:X};')
    lines.append("")
    lines.append(f"}} // namespace fluent::codepoints::{cfg['ns']}")
    lines.append("#endif // __cplusplus")
    lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  [OK] Generated {output_path} ({len(items)} icons, range: 0x{min_cp:X}..0x{max_cp:X})")

def generate_umbrella_header(output_path: str) -> None:
    """Generates IconsFluentSystem.h umbrella header."""
    lines = [
        "// Umbrella header for Microsoft Fluent UI System Icons (Regular & Filled)",
        "// Compatible with Dear ImGui and IconFontCppHeaders",
        "#pragma once",
        "",
        '#include "IconsFluentSystemRegular.h"',
        '#include "IconsFluentSystemFilled.h"',
        "",
        "#if defined(__cplusplus)",
        "namespace fluent {",
        "    namespace reg = regular;",
        "    namespace fill = filled;",
        "",
        "    namespace cp {",
        "        namespace reg = codepoints::regular;",
        "        namespace fill = codepoints::filled;",
        "    }",
        "} // namespace fluent",
        "#endif // __cplusplus",
        "",
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  [OK] Generated umbrella header {output_path}")

# =============================================================================
# Main Driver
# =============================================================================

def main() -> int:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pkg_root = os.path.abspath(os.path.join(script_dir, ".."))

    default_output_dir = os.path.join(pkg_root, "include/fluent_icons")
    default_fonts_dir = os.path.join(pkg_root, "fonts")

    parser = argparse.ArgumentParser(
        description="Download Fluent UI System Icons and generate C/C++ headers."
    )
    parser.add_argument(
        "--output-dir",
        default=default_output_dir,
        help=f"Directory to output generated C++ headers (default: {default_output_dir})",
    )
    parser.add_argument(
        "--fonts-dir",
        default=default_fonts_dir,
        help=f"Directory to store downloaded TTF/JSON files (default: {default_fonts_dir})",
    )
    parser.add_argument(
        "--res-fonts-dir",
        default=None,
        help="Optional external assets/fonts directory to sync TTF files (default: None)",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-downloading files even if they already exist locally",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Skip downloading and only generate headers from existing local files",
    )
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    fonts_dir = os.path.abspath(args.fonts_dir)
    res_fonts_dir = os.path.abspath(args.res_fonts_dir) if args.res_fonts_dir else None

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(fonts_dir, exist_ok=True)
    if res_fonts_dir:
        os.makedirs(res_fonts_dir, exist_ok=True)
    print("==================================================================")
    print("Fluent UI System Icons Generator")
    print("==================================================================")
    print(f"Output Headers : {output_dir}")
    print(f"Fonts Directory: {fonts_dir}")
    if res_fonts_dir:
        print(f"Res Fonts Sync : {res_fonts_dir}")
    print("")

    for variant_key, cfg in FONTS.items():
        print(f"[*] Processing {variant_key.capitalize()} icons...")
        ttf_dest = os.path.join(fonts_dir, cfg["ttf"])
        json_dest = os.path.join(fonts_dir, cfg["json"])

        # 1. Download TTF and JSON
        if not args.no_download:
            download_file(cfg["ttf"], ttf_dest, MIRRORS, force=args.force_download)
            download_file(cfg["json"], json_dest, MIRRORS, force=args.force_download)

        # 2. Sync to external res/fonts if requested
        if res_fonts_dir and os.path.exists(ttf_dest):
            res_ttf_dest = os.path.join(res_fonts_dir, cfg["ttf"])
            shutil.copy2(ttf_dest, res_ttf_dest)
            print(f"  [OK] Synced {cfg['ttf']} to {res_ttf_dest}")
        # 3. Load icon mapping: Prefer JSON, fallback to TTF cmap/post tables
        icons_data: Dict[str, int] = {}

        if os.path.exists(json_dest) and os.path.getsize(json_dest) > 0:
            try:
                with open(json_dest, "r", encoding="utf-8") as f:
                    icons_data = json.load(f)
                print(f"  [OK] Loaded {len(icons_data)} icons from JSON metadata")
            except Exception as e:
                print(f"  [WARN] Failed to parse {json_dest}: {e}")

        if not icons_data and os.path.exists(ttf_dest):
            print(f"  [*] Parsing TTF cmap and post tables from {ttf_dest}...")
            char_to_glyph, glyph_to_name = parse_ttf_tables(ttf_dest)
            for cp, gid in char_to_glyph.items():
                name = glyph_to_name.get(gid)
                if name:
                    icons_data[name] = cp
                else:
                    icons_data[f"ic_fluent_u{cp:04x}{cfg['suffix']}"] = cp
            print(f"  [OK] Extracted {len(icons_data)} glyph mappings from TTF tables")

        if not icons_data:
            print(f"  [ERROR] No icon data available for {variant_key}!")
            return 1

        # 4. Generate variant header
        header_path = os.path.join(output_dir, cfg["header"])
        generate_variant_header(variant_key, icons_data, header_path)
        print("")

    # 5. Generate umbrella header
    umbrella_path = os.path.join(output_dir, "IconsFluentSystem.h")
    generate_umbrella_header(umbrella_path)
    print("")

    print("==================================================================")
    print("Fluent UI System Icons generation completed successfully!")
    print("==================================================================")
    return 0

if __name__ == "__main__":
    sys.exit(main())
