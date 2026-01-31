# Disable External Login

A Home Assistant custom integration that blocks login attempts from external networks while allowing existing authenticated sessions to work from any location.

Easier than VPN or Cloud Flare tunnel. Install, enable and it will work for your whole family!

## What it does

- Blocks new login attempts (`/auth/login_flow`, `/auth/authorize`) from IP addresses outside your configured local networks
- Existing sessions, token refreshes, API calls, and WebSocket connections continue to work from any IP
- Nabu Casa cloud connections are not affected (they appear as local)

## What is NOT blocked

- `POST /auth/token` (token refresh) -- existing sessions keep working
- All authenticated API and WebSocket requests
- Any request originating from a configured local network IP

## Installation

### HACS (recommended)

1. Open HACS in your Home Assistant instance
2. Click the three dots in the top right corner and select **Custom repositories**
3. Add `https://github.com/raivisdejus/ha-disable-external-login` with category **Integration**
4. Search for **Disable External Login** in the list of available repositories on HACS
5. Click **Download**
6. Restart Home Assistant

### Manual

1. Copy the `custom_components/disable_external_login` folder into your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant

## Configuration

1. Go to **Settings** > **Devices & services**
2. Click **+ Add integration**
3. Search for **Disable External Login**
4. Configure:
   - **Enable external login blocking** -- toggle on/off
   - **Local networks** -- add CIDR entries for your local networks (e.g., `192.168.1.0/24`, `10.0.0.0/8`)
5. Submit

Default local networks (RFC 1918 + loopback):
- `127.0.0.0/8`
- `10.0.0.0/8`
- `172.16.0.0/12`
- `192.168.0.0/16`
- `::1/128`
- `fd00::/8`
- `fe80::/10`

Settings can be changed at any time via **Configure** on the integration card without restarting Home Assistant.

## How it works

The integration installs an aiohttp middleware into the Home Assistant HTTP server. The middleware checks `request.remote` (resolved by HA's forwarded middleware using trusted proxy configuration) against the configured local network CIDRs. Requests to login endpoints from non-local IPs receive a 403 response.

## Requirements

- Home Assistant 2024.1.0 or newer
- Trusted proxies must be correctly configured in `configuration.yaml` if running behind a reverse proxy, so that `request.remote` reflects the real client IP

---

Made with Claude Code. If you find this integration useful, please star the repository 🌟