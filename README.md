# VibeProxy - Cross-Platform Desktop Application

VibeProxy is a cross-platform desktop application for managing Bifrost-enhanced AI routing and SLM services.

## Architecture

```
vibeproxy/
├── apps/
│   ├── macos/          # Swift/SwiftUI (macOS 13+)
│   ├── windows/        # WinUI3/C# (Windows 11+)
│   └── linux/          # GTK4/Rust (Linux - optional)
├── shared/
│   ├── core/           # Rust library with FFI bindings
│   └── bindings/       # Platform-specific FFI bindings
│       ├── swift/      # Swift bindings
│       ├── csharp/     # C# bindings
│       └── c/          # C headers
├── proto/              # Shared protocol definitions
└── scripts/            # Build scripts
```

## Building

### Prerequisites

- **macOS**: Xcode 14+, Swift 5.9+
- **Windows**: Visual Studio 2022, .NET 8 SDK
- **Linux**: Rust, GTK4 development libraries
- **All platforms**: Rust toolchain (for shared core)

### Build All Platforms

```bash
./scripts/build-all.sh
```

### Build macOS Only

```bash
./scripts/build-macos.sh
```

### Build Windows (PowerShell)

```powershell
.\scripts\build-windows.ps1
```

## Development

### Shared Core (Rust)

The shared core library provides cross-platform logic:

- Backend client (HTTP client to bifrost-enhanced)
- SLM client (HTTP client to SLM server)
- Configuration management
- Tunnel management (Cloudflare)

```bash
cd shared/core
cargo build
cargo test
```

### macOS App

```bash
cd apps/macos
swift build
swift run
```

## Platform-Specific Features

### macOS
- Menu bar application
- Keychain integration for credentials
- Native SwiftUI interface

### Windows
- System tray application
- Windows Credential Manager integration
- Native WinUI3 interface

### Linux
- System tray (via AppIndicator)
- Keyring integration
- GTK4 interface

## Configuration

Configuration is managed through the shared core library and can be:
- Loaded from JSON files
- Managed via platform-specific settings UI
- Synced across devices (future)

## License

See LICENSE file.
