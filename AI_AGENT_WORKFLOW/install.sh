#!/usr/bin/env bash
set -euo pipefail

REPO="nobletimefashion-pixel/Agentic-AI-"
BRANCH="main"
INSTALL_DIR="${HOME}/.nexus-agent"

echo "Installing Nexus Agent..."

# install uv if missing
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # reload PATH
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

# clone or update repo
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH"
else
    git clone --depth 1 --branch "$BRANCH" "https://github.com/${REPO}.git" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# create isolated venv if missing
if [ ! -d ".venv" ]; then
    uv venv
fi

# activate & install
source .venv/bin/activate
uv pip install -e .

# symlink binary
mkdir -p "${HOME}/.local/bin"
ln -sf "$INSTALL_DIR/.venv/bin/nexus" "${HOME}/.local/bin/nexus"

# add to PATH if not already present
if ! echo "$PATH" | tr ':' '\n' | grep -q "${HOME}/.local/bin"; then
    shell_rc="${HOME}/.bashrc"
    case "${SHELL}" in
        */zsh) shell_rc="${HOME}/.zshrc" ;;
        */fish) shell_rc="${HOME}/.config/fish/config.fish" ;;
    esac
    echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$shell_rc"
    echo "Added ~/.local/bin to PATH in $shell_rc"
fi

echo ""
echo "Nexus Agent installed successfully!"
echo "Run 'nexus' to start."
