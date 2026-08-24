#!/usr/bin/env bash
# Install gobs for the current user.
#   curl -fsSL https://raw.githubusercontent.com/wisdom-km/gobs/main/install.sh | bash
set -euo pipefail
python3 -m pip install --user --upgrade "git+https://github.com/wisdom-km/gobs.git"
BIN="${HOME}/.gobs/bin"
mkdir -p "$BIN"
cat > "$BIN/gobs" <<'EOF'
#!/usr/bin/env bash
exec python3 -m gobs "$@"
EOF
chmod +x "$BIN/gobs"
case ":$PATH:" in
  *":$BIN:"*) ;;
  *) echo "Add to PATH:  export PATH=\"$BIN:\$PATH\"" ;;
esac
echo "Installed. Try:  gobs doctor"
echo "First vault:     gobs init /path/to/vault"
