#!/bin/bash
# AKLP CLI Installer
# Usage: curl -sSL https://raw.githubusercontent.com/next-gen-dist-sys/aklp-cli/main/install.sh | sh

set -e

# Configuration
REPO="next-gen-dist-sys/aklp-cli"
BINARY_NAME="aklp"
INSTALL_DIR="${AKLP_INSTALL_DIR:-$HOME/.local/bin}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Detect OS
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        MINGW*|MSYS*|CYGWIN*) echo "windows";;
        *)          error "Unsupported operating system: $(uname -s)";;
    esac
}

# Detect architecture
detect_arch() {
    case "$(uname -m)" in
        x86_64|amd64)   echo "x64";;
        arm64|aarch64)  echo "arm64";;
        *)              error "Unsupported architecture: $(uname -m)";;
    esac
}

# Get latest version from GitHub
get_latest_version() {
    curl -sSL "https://api.github.com/repos/${REPO}/releases/latest" | \
        grep '"tag_name":' | \
        sed -E 's/.*"([^"]+)".*/\1/'
}

# Download and install
install() {
    local os=$(detect_os)
    local arch=$(detect_arch)
    local version="${AKLP_VERSION:-$(get_latest_version)}"

    if [ -z "$version" ]; then
        error "Failed to detect latest version. Please specify AKLP_VERSION environment variable."
    fi

    info "Installing AKLP CLI ${version}..."
    info "OS: ${os}, Architecture: ${arch}"

    # Build asset name
    local asset_name="${BINARY_NAME}-${os}-${arch}"
    if [ "$os" = "windows" ]; then
        asset_name="${asset_name}.exe"
    fi

    # macOS x64 uses macos-13 runner which produces macos-x64
    local download_url="https://github.com/${REPO}/releases/download/${version}/${asset_name}"

    info "Downloading from: ${download_url}"

    # Create install directory
    mkdir -p "$INSTALL_DIR"

    # Download binary
    local tmp_file=$(mktemp)
    if ! curl -sSL -o "$tmp_file" "$download_url"; then
        rm -f "$tmp_file"
        error "Failed to download binary. Check if the release exists for your platform."
    fi

    # Install binary
    local install_path="${INSTALL_DIR}/${BINARY_NAME}"
    if [ "$os" = "windows" ]; then
        install_path="${install_path}.exe"
    fi

    mv "$tmp_file" "$install_path"
    chmod +x "$install_path"

    success "AKLP CLI installed to: ${install_path}"

    # Check if install dir is in PATH
    if ! echo "$PATH" | tr ':' '\n' | grep -q "^${INSTALL_DIR}$"; then
        echo ""
        warn "${INSTALL_DIR} is not in your PATH."
        echo ""
        echo "Add the following line to your shell configuration file:"
        echo ""
        case "$SHELL" in
            */zsh)
                echo "  echo 'export PATH=\"\$PATH:${INSTALL_DIR}\"' >> ~/.zshrc"
                echo "  source ~/.zshrc"
                ;;
            */bash)
                echo "  echo 'export PATH=\"\$PATH:${INSTALL_DIR}\"' >> ~/.bashrc"
                echo "  source ~/.bashrc"
                ;;
            *)
                echo "  export PATH=\"\$PATH:${INSTALL_DIR}\""
                ;;
        esac
        echo ""
    fi

    # Verify installation
    if [ -x "$install_path" ]; then
        success "Installation complete! Run 'aklp --help' to get started."
    else
        error "Installation failed. Binary is not executable."
    fi
}

# Uninstall
uninstall() {
    local install_path="${INSTALL_DIR}/${BINARY_NAME}"
    if [ -f "$install_path" ]; then
        rm -f "$install_path"
        success "AKLP CLI uninstalled."
    else
        warn "AKLP CLI is not installed at ${install_path}"
    fi
}

# Main
case "${1:-install}" in
    install)
        install
        ;;
    uninstall)
        uninstall
        ;;
    *)
        echo "Usage: $0 {install|uninstall}"
        exit 1
        ;;
esac