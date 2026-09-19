# AGENTS.md - Guide for AI Coding Agents

## Project Overview

**CadreSelecteur** is a Python/Tkinter GUI application for PiBooth photobooth software that allows users to:
1. Select and preview frame templates
2. Create and edit custom frames using a layer-based image editor
3. Manage frame layouts with text, images, and geometric exclusion zones

The application is packaged as both a Python module and standalone executables (Windows/Linux via PyInstaller).

## Architecture & Data Flow

### Three Main Entry Points

1. **Frame Selector** (`CadreSelecteur.cadreselecteur.CadreSelecteur`)
   - Main GUI: displays available frames (left sidebar) and installed frame (right sidebar)
   - Allows selecting which frame template PiBooth will use next
   - Runs in main process with splash screen

2. **Frame Editor** (`CadreSelecteur.CadreEditeur.imageeditorapp.ImageEditorApp`)
   - Layer-based image editor accessible from frame selector via "Nouveau" button
   - Creates custom frames with composable layers: images, text, exclusion zones
   - Loads/saves projects as JSON; exports as PNG

3. **Main Entry** (`CadreSelecteur.__main__`)
   - Spawns splash process and app process via multiprocessing
   - Validates mandatory directories (Templates/, Cadres/, Fonts/) before starting GUI

### Directory Structure & Responsibilities

```
CadreSelecteur/
├── cadreselecteur.py        → Frame selector UI + frame operations
├── cadreediteur.py          → Entry point for frame editor
├── config_loader.py         → Loads config from resources/config.json (with PyInstaller fallback)
├── logging_config.py        → Centralized logging (writes to resources/image_editor.log)
├── i18n/
│   └── translator.py        → Translation system: _t(key, **kwargs)
├── CadreEditeur/
│   ├── imageeditorapp.py    → Frame editor main window + layer lifecycle
│   ├── imageeditor.py       → Canvas rendering + layer manipulation
│   ├── layer.py             → Base Layer class (drag, visibility, locking)
│   ├── layertext.py         → Text layer with fonts from Fonts/ directory
│   ├── layerimage.py        → Image layer (import & scale)
│   └── layerexcluzone.py    → Exclusion zone layer (transparency mask)
├── Templates/               → Available frame templates (XML + PNG preview)
├── Cadres/                  → Selected frame (symlink/copy target for PiBooth)
├── Fonts/                   → TTF/OTF fonts for LayerText
├── resources/
│   ├── config.json          → Configuration (window size, thumbnail sizes, language)
│   ├── image_editor.log     → Logging output
│   └── {fr,en,...}.json     → i18n translation files
```

## Critical Patterns & Conventions

### 1. PyInstaller Compatibility (High Priority)

All path resolution must handle THREE execution contexts:
- **Mode 1**: Normal Python execution (`python3 -m CadreSelecteur`)
- **Mode 2**: PyInstaller frozen binary (resources bundled in temp `_MEIPASS`)
- **Mode 3**: Development (resources in `CadreSelecteur/resources/`)

**Pattern in use**:
```python
if getattr(sys, 'frozen', False):
    # PyInstaller context: check _MEIPASS first, fallback to tempdir
    MEIPASS_DIR = Path(getattr(sys, '_MEIPASS', ''))
    # Try multiple candidate paths under _MEIPASS
else:
    # Normal execution: use relative package paths
    RESOURCES_DIR = BASE_DIR / 'resources'
```

Files implementing this: `config_loader.py`, `logging_config.py`, `translator.py`, `layertext.py`, `cadreselecteur.py`

**Rule**: When adding file loading (fonts, images, configs), always add PyInstaller fallback logic.

### 2. Centralized i18n (Single Source of Truth)

- **API**: `from CadreSelecteur.i18n import t, set_language, get_language` (or `_t` from submodules)
- **Translation files**: JSON in `resources/{lang}.json` (currently `fr.json`)
- **Key format**: Hierarchical with dots: `"selector.label.available_frames"`, `"image.button.add_image"`
- **Lazy loading**: Translations load only when needed via `set_language()`

**Pattern**: Use `_t('key')` in all UI strings; configure language in `config.json` (default `"fr"`)

Files: `CadreSelecteur/i18n/translator.py`, `resources/{lang}.json`

### 3. Layer Architecture (Core to Frame Editor)

**Inheritance tree**:
```
Layer (base class - position, visibility, locking)
├── LayerImage (drag+scale images, original aspect ratio always locked)
├── LayerText (render fonts, font selection via FileBrowser, size clamped to [4, 200])
└── LayerExcluZone (transparency mask for frame borders, template-driven, NOT editable)
```

**Data flow**:
1. **ImageEditorApp** maintains `app.layers` list (stack order) + `app.active_layer_idx`
2. **ImageEditor** handles canvas rendering and layer manipulation
3. Each layer type has `render()` method returning PIL Image for export
4. Canvas coordinates (`CANVA_*`) vs. Image coordinates (`IMAGE_*`) with `RATIO` multiplier

**Key invariant**: All coordinates scale by `RATIO` (canvas → image space)

Example: `LayerImage.resize()` updates both display and image position

**Param-zone editing (two-way sync)**:
- `Layer.set_display_position(x, y)` — sets canvas position + syncs export position (× `RATIO`).
- `LayerImage`: editable X/Y/W/H entries (`set_position`/`set_size`); H is always
  recomputed from the **original** image aspect (master = field that changed vs current size).
- `LayerText`: editable X/Y/font-size entries (`set_position`/`set_font_size`);
  size clamped to `[MIN_FONT_SIZE, MAX_FONT_SIZE]` = [4, 200] (see Gotchas).
- `LayerExcluZone.update_param_zone()` is display-only (zones come from the XML template).
- Live update: entries use `trace_add('write')` (silent, invalid keystrokes ignored) +
  `<Return>`/`<FocusOut>` (with validation dialogs). No "Apply" buttons.
- Mouse → fields: `ImageEditor.drag_drop()`/`resize()` call `layer.sync_param_zone()`
  after `update_canvas()`.
- **Anti-recursion**: programmatic var writes run under `self._syncing = True`;
  live trace handlers must return early when set (else keystroke → set → trace → loop).
- `param_frame` is 250×300 (`pack_propagate(False)`); keep new controls compact
  (square buttons `width=2`, side-by-side rows).

**Rendering performance rules**:
- `LayerImage.resize()`/`set_size()` rebuild ONLY the display-size image and set
  `_export_dirty = True`; the 3× export image is rebuilt on demand in
  `draw_on_image(export=True)` via `_ensure_export_image()`. Never resize the
  export image on interactive paths (wheel/drag/typing).
- `LayerText` caches `pil_font` (display) + `pil_font_export` (× `RATIO`) via
  `_rebuild_fonts()` — called on every font/size change, never per-draw.
  Never call `ImageFont.truetype()` inside `draw_on_image()`.
- `ImageEditor.drag_drop()` redraws via `request_canvas_update()` (`after_idle`
  coalescing: N motion events → 1 redraw). Wheel resize stays synchronous.

### 4. Configuration Loading (Runtime Defaults)

- **Source**: `resources/config.json` (JSON dict with keys: `WINDOWS_SIZE`, `THUMBNAIL_H`, `LANGUAGE`, etc.)
- **Fallback**: Hardcoded `_defaults` dict if file missing or invalid
- **Export**: Constants like `WINDOWS_SIZE`, `THUMBNAIL_H` exported from `config_loader.py`
- **Error handling**: Logs warnings, uses defaults on parse errors

**Pattern**: All runtime config constants should be loaded in `config_loader.py`, not scattered

### 5. Logging Strategy

- **Centralized setup**: `logging_config.py` ensures FileHandler writes to `resources/image_editor.log`
- **PyInstaller**: Uses tempdir (`tempfile.gettempdir() / 'CadreSelecteur'`) to avoid _MEIPASS read-only issues
- **Package logger**: `logging.getLogger('CadreSelecteur')` prevents duplicate handlers
- **CLI fallback**: Root logger gets StreamHandler if no handlers exist

**Rule**: Import `from CadreSelecteur.logging_config import LOG_PATH` at package init to ensure setup

### 6. Project/Frame Serialization

**Frame Editor state** (`.json` files):
- Stores layer list with type, properties (text, font, image path, color, position, size)
- Loaded/saved via `json.dump()` and `json.load()`
- Converted to PNG frames via `ImageEditor.export()` + layer `render()` methods

**Templates** (`.xml` files):
- XML format defining exclusion zones for frame borders
- Parsed at editor startup: `ET.parse()` → extract exclusion coords
- Example: `template_1.xml` defines borders for 1-photo frame; `template.xml` for 4-photo layout

**Key distinction**: Projects (`.json`) are editor state; Templates (`.xml`) are frame layouts

## Developer Workflows

### Running & Testing

```bash
# Run application from source
python3 -m CadreSelecteur

# Run tests
python3 run_tests.py

# Build standalone executables (Windows + Linux)
make linux    # Linux binary
make windows  # Windows .exe
make clean    # Clean build artifacts
```

### Adding New Translations

1. Add key-value pairs to `CadreSelecteur/resources/fr.json` (and future lang files)
2. Use `_t('new.key')` in code
3. No recompile needed; translation picked up at runtime

### Adding Layer Types

1. Inherit from `Layer` base class in new file `CadreSelecteur/CadreEditeur/layer{type}.py`
2. Implement `render(bg_color=None)` → PIL Image
3. Register in `ImageEditorApp.__init__()` and `clean_editable_layer()`
4. Add UI button in `ImageEditor.__init__()`

### Debugging PyInstaller Issues

- Check `build/CadreSelecteur/warn-CadreSelecteur.txt` for missing imports
- Verify paths in `CadreSelecteur.spec` include all data files
- Test executable with: `./CadreSelecteur` (Linux) or `CadreSelecteur.exe` (Windows)

## Integration Points & Dependencies

### External Libraries

- **Pillow**: Image loading, rendering, font handling
- **matplotlib**: Numerical operations (NumPy-based)
- **fontTools**: Font metrics (used indirectly)
- **Tkinter**: Built-in GUI (Python 3.7+)

### File System Expectations

PiBooth expects frame selection result at `Cadres/cadre_1.png` or `Cadres/cadre_4.png` (1-photo or 4-photo layout)

### Multiprocessing Behavior

- Splash screen runs in separate process
- Main app in separate process (prevents freeze during startup)
- Communicate via file system only (no queues/pipes needed)

## Common Gotchas & Fixes

| Issue | Root Cause | Solution |
|-------|-----------|----------|
| Fonts not loading in .exe | Path to Fonts/ incorrect for PyInstaller | Check `layertext.py` PyInstaller fallbacks |
| Config not persisting | Writing to read-only _MEIPASS | All writes must go to tempdir or user data dir |
| Translations missing | Language file not in resources/ | Ensure `resources/{lang}.json` exists and is valid JSON |
| Canvas not rendering | Layer coordinates using wrong scale (display vs. image) | Check `RATIO` multiplication in layer coordinate methods |
| Blocking error-popup cascade | Huge font size (typed, font-chooser, or loaded JSON) makes PIL allocate giant glyph bitmaps on every redraw | Font size is clamped to [4, 200] (`clamp_font_size`, enforced in setters, `from_dict`, `callback_font`, `draw_on_image`); keep the clamp |
| Trace recursion / redundant redraws | Setting entry StringVars programmatically fires `trace_add('write')` handlers | Wrap programmatic sets with `self._syncing = True` + early return in live handlers |
| Tests fail with i18n errors | Import order issue or missing test setup | Run tests with `python3 run_tests.py` (sets up logging) |

## Key Files Reference

| File | Purpose | Stability |
|------|---------|-----------|
| `config_loader.py` | Runtime configuration | Stable (core infrastructure) |
| `logging_config.py` | Centralized logging | Stable |
| `cadreselecteur.py` | Main selector UI | Active (main feature) |
| `imageeditorapp.py` | Editor window lifecycle | Active (main feature) |
| `layer.py` + `layer*.py` | Layer model | Moderate (growing feature) |
| `i18n/translator.py` | Translation API | Stable |
| `resources/config.json` | User settings | Evolving |

---

**Last Updated**: 2026-09-19  
**Python**: 3.10+  
**Maintainer Concerns**: PyInstaller compatibility, i18n consistency, layer architecture scalability

