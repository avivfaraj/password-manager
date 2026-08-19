# Running Password Manager in Docker

## Prerequisites

This GUI application requires X11 display forwarding. The setup is now simplified - just mount the X11 socket!

### System Requirements
- Docker installed
- XQuartz running on macOS (or native X11 on Linux)

## Quick Start

### macOS

1. **Ensure XQuartz is running:**
   ```bash
   open -a XQuartz
   ```

2. **Enable network connections in XQuartz:**
   - Go to **XQuartz → Preferences → Security**
   - Enable "Allow connections from network clients"
   - Restart XQuartz (quit and reopen)

3. **Run the container:**
   ```bash
   docker compose up
   ```

### Linux

Simply run:
```bash
docker compose up
```

The container connects to your X server using the configured `DISPLAY` environment variable.

## How It Works

The `docker-compose.yml` configures the `DISPLAY` environment variable and mounts the
application data directory for persistence.

## Building the Docker Image

```bash
docker build -t pm:dev .
```

## Running the Container

### Using Docker Compose (Recommended)
```bash
docker compose up
```

To run in the background:
```bash
docker compose up -d
```

To stop the containers:
```bash
docker compose down
```

### Using Docker CLI

**macOS:**
```bash
docker run --rm \
  -e DISPLAY=:0 \
  pm:dev
```

**Linux:**
```bash
docker run --rm \
  -e DISPLAY=$DISPLAY \
  pm:dev
```

## Troubleshooting

### "couldn't connect to display ":0""

**For macOS:**
1. Verify XQuartz is running: `open -a XQuartz`
2. Check Security settings: XQuartz → Preferences → Security → "Allow connections from network clients" ✅
3. **Restart XQuartz** (quit and reopen)
4. Verify the socket exists: `ls -la /tmp/.X11-unix/`
5. Try again: `docker compose up`

**For Linux:**
1. Verify X11 is running: `echo $DISPLAY`
2. Check the socket exists: `ls -la /tmp/.X11-unix/`
3. Try: `docker compose up`

### "Permission denied" on X11 socket

The container user needs access to the X11 socket. Try:

```bash
# Make socket world-readable (temporary, resets on X11 restart)
chmod 777 /tmp/.X11-unix/0
chmod 777 /tmp/.X11-unix
```

Then try again.

### Container exits immediately

Run in the foreground to see errors:
```bash
docker compose up --no-detach
```

Or check logs:
```bash
docker compose logs password-manager
```

## Notes

- The container runs as a non-root user (`appuser`) for security
- Build dependencies are removed after installation to keep image size minimal
- Persistent data can be stored in the `./data` volume
