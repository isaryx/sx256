#!/usr/bin/env python3
"""Convert sx_256.keymap comment rows to keymap-drawer YAML."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

KEY_LABELS = {
    "ESC": "Esc",
    "BSPC": "$$mdi:backspace$$",
    "DEL": "$$mdi:backspace-reverse-outline$$",
    "RETURN": "$$mdi:keyboard-return$$",
    "RET": "$$mdi:keyboard-return$$",
    "SPACE": "$$mdi:keyboard-space$$",
    "TAB": "$$mdi:keyboard-tab$$",
    "LSHFT": "$$mdi:apple-keyboard-shift$$",
    "RSHFT": "$$mdi:apple-keyboard-shift$$",
    "LCTRL": "$$mdi:apple-keyboard-control$$",
    "RCTRL": "$$mdi:apple-keyboard-control$$",
    "LALT": "$$mdi:apple-keyboard-option$$",
    "RALT": "$$mdi:apple-keyboard-option$$",
    "LGUI": "$$mdi:apple-keyboard-command$$",
    "RGUI": "$$mdi:apple-keyboard-command$$",
    "SEMI": ";",
    "SQT": "'",
    "COMMA": ",",
    "DOT": ".",
    "SLASH": "/",
    "MINUS": "-",
    "EQUAL": "=",
    "GRAVE": "`",
    "LBKT": "[",
    "RBKT": "]",
    "LBRC": "{",
    "RBRC": "}",
    "BSLH": "\\",
    "PIPE": "|",
    "LPAR": "(",
    "RPAR": ")",
    "C_MUTE": "$$mdi:volume-off$$",
    "SLCK": "Slck",
    "PG_UP": "Page Up",
    "PG_DN": "Page Down",
    "CAPS": "$$mdi:apple-keyboard-caps$$",
    "HOME": "Home",
    "END": "End",
    "LEFT": "←",
    "RIGHT": "→",
    "UP": "↑",
    "DOWN": "↓",
    "BTCLR": "BT clr",
    "OUTBLE": "$$mdi:bluetooth$$",
    "OUTUSB": "$$mdi:usb$$",
    "RESET": "Reset",
    "FLASH": "Flash",
    "VOL_UP": "Vol+",
    "VOL_DN": "Vol-",
    "MUTE": "$$mdi:volume-off$$",
    "PLAY": "$$mdi:play-pause$$",
    "PREV": "Prev",
    "NEXT": "Next",
    "T_H": "⌃A",
    "T_WB": "⌥B",
    "T_WF": "⌥F",
    "T_E": "⌃E",
    "C_Z": "⌃Z",
    "C_X": "⌃X",
    "C_C": "⌃C",
    "C_V": "⌃V",
}

TRANS = '""'
EMPTY = TRANS
BLANK = "{type: none}"
LAYER_RE = re.compile(r"\{t: ([^,}]+), type: layer\}$")
MOD_RE = re.compile(r"\{t: (?:(?:'((?:[^']|'')*)')|([^,}]+)), type: mod\}$")
MODIFIER_CODES = frozenset({"LCTRL", "RCTRL", "LALT", "RALT", "LGUI", "RGUI"})
ARROW_CODES = frozenset({"LEFT", "RIGHT", "UP", "DOWN"})
MOD_GLYPHS = frozenset(
    {
        "$$mdi:apple-keyboard-control$$",
        "$$mdi:apple-keyboard-option$$",
        "$$mdi:apple-keyboard-command$$",
    }
)
ARROW_LABELS = frozenset({"←", "→", "↑", "↓"})


def typed_entry(label: str, type_name: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_+]+$", label):
        return f"{{t: {label}, type: {type_name}}}"
    escaped = label.replace("'", "''")
    return f"{{t: '{escaped}', type: {type_name}}}"


def layer_entry(layer: str) -> str:
    return typed_entry(layer, "layer")


def is_mod_code(code: str) -> bool:
    return code in MODIFIER_CODES or code in ARROW_CODES


def mod_entry(label: str) -> str:
    return typed_entry(label, "mod")


def bt_entry(n: str) -> str:
    profile = str(int(n) + 1)
    type_name = "bt_sym mod" if profile in ("1", "2", "3") else "bt_sym"
    return (
        f"{{t: '$$mdi:bluetooth-connect$$', s: '{profile}', type: '{type_name}'}}"
    )


def trans_entry(label: str) -> str:
    if label in (EMPTY, '""'):
        return EMPTY
    m = LAYER_RE.match(label)
    if m:
        return f"{{t: {m.group(1)}, type: trans}}"
    m = MOD_RE.match(label)
    if m:
        tap = (m.group(1) or m.group(2)).replace("''", "'")
        if re.fullmatch(r"[A-Za-z0-9_+]+$", tap):
            return f"{{t: {tap}, type: trans}}"
        escaped = tap.replace("'", "''")
        return f"{{t: '{escaped}', type: trans}}"
    if label in MOD_GLYPHS or label in ARROW_LABELS:
        return f"{{t: '{label}', type: trans}}"
    if re.fullmatch(r"[A-Za-z0-9_+]+$", label):
        return f"{{t: {label}, type: trans}}"
    escaped = label.replace("'", "''")
    return f"{{t: '{escaped}', type: trans}}"


def label_key(code: str) -> str:
    if code.startswith("N") and code[1:].isdigit():
        return code[1:]
    if code.startswith("F") and code[1:].isdigit():
        return code
    return KEY_LABELS.get(code, code)


def token_to_yaml(token: str) -> str:
    if token in ("_____", "&none"):
        return BLANK
    if token == "&trans":
        raise ValueError("resolve &trans before calling token_to_yaml")
    if token.startswith("&mo"):
        return layer_entry(token.rsplit(" ", 1)[-1])
    if token in ("&bootloader", "FLASH"):
        return "{t: '$$mdi:progress-download$$', type: bootloader}"
    if token in ("&sys_reset", "RESET"):
        return "{t: '$$mdi:backup-restore$$', type: bootloader}"
    if token.startswith("L_CMD("):
        key = token[6:-1]
        return f"⌘{label_key(key)}"
    if token.startswith("BT("):
        return bt_entry(token[3:-1])
    if token in ("BTCLR", "OUTBLE", "OUTUSB"):
        return label_key(token)
    if token in ("VOL_UP", "VOL_DN", "MUTE", "PLAY", "PREV", "NEXT", "T_H", "T_WB", "T_WF", "T_E"):
        return label_key(token)
    if token == "_":
        raise ValueError("dangling _ macro")
    if token.startswith("_"):
        code = token[1:]
        label = label_key(code)
        return mod_entry(label) if is_mod_code(code) else label
    label = label_key(token)
    return mod_entry(label) if is_mod_code(token) else label


def parse_row(line: str) -> list[str]:
    body = line.split("*/", 1)[1] if "*/" in line else line
    tokens = body.split()
    out: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "&mo" and i + 1 < len(tokens):
            out.append(f"&mo {tokens[i + 1]}")
            i += 2
            continue
        if tok == "_" and i + 1 < len(tokens):
            out.append(f"_{tokens[i + 1]}")
            i += 2
            continue
        if tok.startswith("L_CMD("):
            out.append(tok)
            i += 1
            continue
        if tok.startswith("BT("):
            out.append(tok)
            i += 1
            continue
        out.append(tok)
        i += 1
    return out


def resolve_key(
    raw_layers: dict[str, list[str]],
    layer_order: list[str],
    layer_idx: int,
    key_idx: int,
) -> str:
    for li in range(layer_idx, -1, -1):
        token = raw_layers[layer_order[li]][key_idx]
        if token == "&trans":
            continue
        if token in ("_____", "&none"):
            return BLANK
        label = token_to_yaml(token)
        if li < layer_idx:
            return trans_entry(label)
        return label
    return EMPTY


def resolve_layers(
    raw_layers: dict[str, list[str]], layer_order: list[str]
) -> dict[str, list[str]]:
    resolved: dict[str, list[str]] = {}
    for layer_idx, name in enumerate(layer_order):
        resolved[name] = [
            resolve_key(raw_layers, layer_order, layer_idx, key_idx)
            for key_idx in range(len(raw_layers[name]))
        ]
    return resolved


def parse_keymap(path: Path) -> tuple[list[str], dict[str, list[str]], dict[str, str]]:
    text = path.read_text()
    raw_layers: dict[str, list[str]] = {}
    layer_labels: dict[str, str] = {}
    layer_order: list[str] = []
    current: str | None = None

    for line in text.splitlines():
        m = re.match(r"\s*(\w+_layer)\s*\{", line)
        if m:
            current = m.group(1).replace("_layer", "")
            layer_order.append(current)
            raw_layers[current] = []
            continue
        if current and "display-name" in line:
            dm = re.search(r'display-name\s*=\s*"([^"]+)"', line)
            if dm:
                layer_labels[current] = dm.group(1)
            continue
        if current and ("/*  row" in line or "/*  thumb" in line):
            raw_layers[current].extend(parse_row(line))

    layers = resolve_layers(raw_layers, layer_order)
    return layer_order, layers, layer_labels


def yaml_entry(key: str) -> str:
    if key == BLANK:
        return f"  - {key}"
    if key == '""':
        return '  - ""'
    if (
        re.match(r"\{t: .+, type: trans\}$", key)
        or LAYER_RE.match(key)
        or MOD_RE.match(key)
        or ("mdi:bluetooth-connect" in key and key.startswith("{"))
    ):
        return f"  - {key}"
    if key.startswith("{"):
        return f'  - "{key}"'
    if re.fullmatch(r"[A-Za-z0-9_+]+$", key):
        return f"  - {key}"
    escaped = key.replace("'", "''")
    return f"  - '{escaped}'"


SX256_LAYOUT = (
    "layout: {ortho_layout: {split: true, rows: 4, columns: 6, thumbs: 6}}"
)


def emit_yaml(layer_order: list[str], layers: dict[str, list[str]]) -> str:
    lines = [SX256_LAYOUT, "layers:"]
    for name in layer_order:
        keys = layers[name]
        if len(keys) != 60:
            raise SystemExit(f"layer {name}: expected 60 keys, got {len(keys)}")
        lines.append(f"  {name}:")
        for key in keys:
            lines.append(yaml_entry(key))
    return "\n".join(lines) + "\n"


LAYER_SUFFIX = {
    "base": "BASE",
    "fn1": "FN1",
    "fn2": "FN2",
    "fn3": "FN3",
}


def format_layer_label(layer_id: str, display_name: str) -> str:
    return f"{display_name}({LAYER_SUFFIX[layer_id]})"


def apply_layer_labels(svg: str, layer_labels: dict[str, str]) -> str:
    for layer_id, label in layer_labels.items():
        header = format_layer_label(layer_id, label)
        svg = re.sub(
            rf'(<text[^>]*id="{layer_id}"[^>]*>){layer_id}:',
            rf"\1{header}:",
            svg,
        )
    return svg


def enlarge_command_legends(svg: str) -> str:
    return re.sub(
        r'<text x="0" y="-4" class="([^"]*) tap">(⌘[^<]+)</text>',
        r'<text x="0" y="-4" class="\1 tap" font-size="17">\2</text>',
        svg,
    )


def enlarge_mod_glyphs(svg: str) -> str:
    return re.sub(
        r'(<use\b(?=[^>]*class="key mod tap glyph)[^>]*?)'
        r'x="-9" y="-13" height="18" width="18\.0"',
        r'\1x="-12" y="-17" height="24" width="24.0"',
        svg,
    )


def enlarge_arrow_legends(svg: str) -> str:
    return re.sub(
        r'<text x="0" y="-4" class="([^"]*) tap">([↑↓←→])</text>',
        r'<text x="0" y="-4" class="\1 tap" font-size="20">\2</text>',
        svg,
    )


def write_yaml(root: Path, keymap: Path, out: Path) -> tuple[Path, dict[str, str]]:
    layer_order, layers, layer_labels = parse_keymap(keymap)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(emit_yaml(layer_order, layers))
    print(f"wrote {out} ({len(layer_order)} layers)")
    return out, layer_labels


def draw_svg(
    root: Path, yaml_path: Path, svg_path: Path, layer_labels: dict[str, str]
) -> Path:
    config = root / "keymap_drawer.config.yaml"
    subprocess.run(
        [
            "uv",
            "tool",
            "run",
            "--from",
            "keymap-drawer",
            "keymap",
            "-c",
            str(config),
            "draw",
            str(yaml_path),
            "-o",
            str(svg_path),
        ],
        check=True,
    )
    svg = apply_layer_labels(svg_path.read_text(), layer_labels)
    svg = enlarge_command_legends(svg)
    svg = enlarge_arrow_legends(svg)
    svg = enlarge_mod_glyphs(svg)
    svg_path.write_text(svg)
    print(f"wrote {svg_path}")
    return svg_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--draw",
        action="store_true",
        help="also render SVG with keymap-drawer and normalize thumb keycaps",
    )
    parser.add_argument(
        "--keymap",
        type=Path,
        default=Path("config/boards/shields/sx_256/sx_256.keymap"),
        help="path to ZMK keymap (default: sx_256.keymap)",
    )
    parser.add_argument(
        "--name",
        default="sx_256",
        help="output basename under keymap-drawer/ (default: sx_256)",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    keymap = root / args.keymap
    yaml_path = root / "keymap-drawer" / f"{args.name}.yaml"
    svg_path = root / "keymap-drawer" / f"{args.name}.svg"

    yaml_path, layer_labels = write_yaml(root, keymap, yaml_path)
    if args.draw:
        draw_svg(root, yaml_path, svg_path, layer_labels)


if __name__ == "__main__":
    main()
