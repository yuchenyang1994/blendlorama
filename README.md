# blender-Lorama

<img src="./logo.png" width="50%" alt="Blender-Aseprite Bridge Logo">

[简体中文](README.zh-CN.md) | [English](README.md)

A real-time synchronization tool that connects Blender and Pixelorama for seamless pixel art workflow. This project consists of two components: a Blender addon and a Pixelorama extension that communicate via WebSocket to sync UV maps, textures, and pixel art data in real-time.

## Overview

Blender Pixel Sync enables artists to work with pixel art textures in Blender while having real-time synchronization with Pixelorama. The tool provides pixel-perfect UV unwrapping, texture management, and live updates between both applications.

## Features

### Blender Addon (`blender-part/`)

- **WebSocket Server**: Real-time communication server for data synchronization
- **Pixel-Perfect UV Unwrapping**: Specialized UV unwrapping algorithms for pixel art
- **Texture Management**: Automatic texture detection, loading, and management
- **UV Export/Import**: Export UV layouts to Pixelorama and import back with modifications
- **Image State Monitoring**: Real-time monitoring of image changes in Blender
- **World Grid Tools**: Specialized grid setup for pixel art workflow
- **Checker Texture Generation**: Create checker patterns for texture testing

### Pixelorama Extension (`blender-lorama/`)

- **WebSocket Client**: Connects to Blender's WebSocket server
- **UV Overlay**: Visual overlay showing Blender UV layouts in Pixelorama
- **Texture Export**: Export modified textures back to Blender
- **Sync Panel**: User interface for managing synchronization settings
- **Real-time Updates**: Live updates when textures change in Blender

## Installation

### Blender Addon Installation

1. Download the pre-packaged zip file
2. In Blender, go to `Edit > Preferences > Add-ons`
3. Click "Install..." and select the zip file
4. Enable the "Pixelorama Sync" addon

### Pixelorama Extension Installation

1. Open Pixelorama
2. Go to `Preferences > Extensions > Install Extension`
3. Select the pre-packaged `.pck` file
4. The "BlenderPixelorama" extension will be installed automatically

## Usage

### Setting up the Workflow

1. **Start the Blender Server**:

   - In Blender, open the Image Editor
   - Go to the "Pixelorama Sync" panel (Image Editor > UI Panel > Pixelorama Sync)
   - Click "Start Server" to begin the WebSocket server

2. **Connect from Pixelorama**:

   - In Pixelorama, the Blender Pixel Sync panel will appear as a new tab
   - The extension will automatically attempt to connect to Blender
   - Connection status will be displayed in the panel

3. **Prepare Your Model**:
   - Create or import your 3D model in Blender
   - Apply materials and UV unwrapping
   - Use the pixel-perfect unwrapping tools for optimal results

### Working with Textures

1. **Export UV Layout**:

   - Select your object in Blender
   - Use the UV tools to export the layout to Pixelorama
   - The UV layout will appear as an overlay in Pixelorama

2. **Create/Edit Textures**:

   - Design your pixel art texture in Pixelorama
   - Use the UV overlay as a guide for precise placement
   - The grid setup ensures pixel-perfect alignment

3. **Sync Changes**:
   - Changes in Pixelorama can be exported back to Blender
   - Blender will automatically update the texture
   - Real-time synchronization keeps both applications in sync

### Recommended Workflow

1. **Model Setup**:

   - Create your low-poly model in Blender
   - Use the "Setup World Grid" tool for proper pixel art scaling
   - Set grid subdivisions based on your pixel density requirements

2. **UV Unwrapping**:

   - Use "Pixel Perfect Unwrap" for clean, pixel-aligned UVs
   - Or use "Unwrap to Grid" for grid-based UV layouts
   - Check UVs in the UV Editor for proper alignment

3. **Texture Creation**:
   - Export UV layout to Pixelorama
   - Create pixel art texture following the UV guides
4. **Final Integration**:
   - Export texture back to Blender
   - Apply to model and test in 3D view
   - Make adjustments as needed in either application

## Blender Panel UI

The Blender addon provides several panels:

### Server Panel

- **Start/Stop Server**: Control the WebSocket server
- **Connection Status**: Shows connected clients and server status
- **Port Information**: Display server connection details

### UV Tools Panel

- **Pixel Perfect Unwrap**: Unwrap UVs with pixel-perfect precision
- **Unwrap to Grid**: Create grid-based UV layouts
- **Export UV**: Send UV data to Pixelorama

### Texture Tools Panel

- **Check Texture**: Validate texture dimensions and format
- **Create Checker**: Generate checker pattern textures
- **Reload Textures**: Refresh textures from disk

### World Grid Panel

- **Setup World Grid**: Configure Blender's grid for pixel art
- **Grid Subdivisions**: Adjust grid density
- **Scale Settings**: Set appropriate scale for pixel work

## Compatibility

### Blender

- **Version**: Blender 4.5.0 and later
- **Platform**: Windows, macOS, Linux

### Pixelorama

- **Version**: Supports Pixelorama API version 8
- **Platform**: Windows, macOS, Linux

## Technical Details

### Communication Protocol

- **WebSocket**: Real-time bidirectional communication
- **JSON Message Format**: Structured data exchange
- **Event-Driven**: Automatic updates on changes

### Supported Features

- **Image Formats**: PNG, JPG, BMP, and other Blender-supported formats
- **UV Coordinates**: Full UV map synchronization

## Dependencies

### Blender Addon Dependencies

- `websockets` library (automatically installed by the addon)
- Blender 4.5.0 or later
- NumPy (included with Blender)

### Pixelorama Extension Dependencies

- Pixelorama with extension support
- Godot Engine (Pixelorama runtime)

## File Structure

```
blender-pixel-sync/
├── blender-part/              # Blender addon
│   ├── __init__.py           # Addon registration
│   ├── server.py             # WebSocket server
│   ├── operators.py          # Blender operators
│   ├── blender_integration.py # Blender integration logic
│   ├── uv_extractor.py       # UV extraction and processing
│   ├── image_manager.py      # Image and texture management
│   ├── texture_processor.py  # Texture processing tools
│   ├── unwrap_tools.py       # UV unwrapping algorithms
│   ├── ui.py                 # User interface panels
│   ├── watch.py              # File watching and change detection
│   ├── deps.py               # Dependency management
│   └── libs/                 # Third-party libraries
└── blender-lorama/           # Pixelorama extension
    └── src/
        └── Extensions/
            └── BlenderPixelorama/
                ├── extension.json      # Extension metadata
                ├── Main.gd            # Main extension script
                ├── Main.tscn          # Main scene
                ├── BlenderLoramaPanel.tscn # UI panel
                ├── WebSocketClient.gd # WebSocket client
                ├── uv_overlay.gd      # UV overlay functionality
                ├── blender_lorama_panel.gd # Panel logic
                └── texture_exporter.gd # Texture export
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests, report bugs, or suggest features.

### Development Setup

1. Clone the repository
2. For Blender development: Use Blender's scripting environment
3. For Pixelorama development: Use Godot Engine with Pixelorama source
4. Test changes with both applications running

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Credits

- **Original Author**: Heisenshark
- **Refactored by**: Assistant
- **Pixelorama Extension**: yuchenyang1994
- **UV Unwrapping Algorithm**: Based on Magic-UV by Nutti

## Support

For issues, questions, or support:

1. Check the GitHub issues page
2. Review the documentation for common solutions
3. Provide Blender and Pixelorama versions when reporting issues

## Version History

### v0.1.0

- Initial release
- Basic WebSocket communication
- UV export/import functionality
- Pixel-perfect unwrapping tools
- Texture synchronization
- World grid setup tools
