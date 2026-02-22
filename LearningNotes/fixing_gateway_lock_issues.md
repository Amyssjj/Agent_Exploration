# Fixing OpenClaw Gateway "Already Running" & "Lock Timeout" Issues

When attempting to run or start the OpenClaw gateway, you might encounter recurring errors in the `gateway.err.log` indicating that it failed to start due to an existing process lock, along with occasional `MODULE_NOT_FOUND` errors for `dist/entry.js`. 

This walkthrough documents exactly why this happens and how to clear the stuck processes so the gateway can launch properly.

## Symptoms

- `gateway.err.log` repeatedly shows: `Gateway failed to start: gateway already running (pid XXXX); lock timeout after 5000ms`.
- Running `openclaw gateway start` or loading the LaunchAgent returns successful commands, but the gateway doesn't actually stay online.
- You might see an error that `Error: Cannot find module '.../openclaw/dist/entry.js'`.

## Root Causes

1. **Defunct (Zombie) Processes**: When the OpenClaw gateway process dies abruptly or is killed incorrectly, it can leave behind a defunct process in the process table. Node.js's lockfile checker sees this PID still exists in macOS and continuously fails to acquire the launch lock.
2. **Missing Build Artifacts**: If the gateway is trying to start but crashes immediately with a `MODULE_NOT_FOUND` error for `entry.js`, it means the OpenClaw source directory hasn't been compiled properly (the `dist/` directory is missing).

---

## Step-by-Step Fix

### 1. Verify the OpenClaw Build Exists

Before fighting with process locks, verify that `dist/entry.js` actually exists in your installation directory:

```bash
ls -la ~/openclaw/dist/entry.js
```

If this file does not exist, you must build the project first:
```bash
cd ~/openclaw
pnpm install
pnpm build
```

### 2. Identify the Zombie Process Holding the Lock

If you see `Gateway failed to start: gateway already running (pid 3559)`, use `ps` to find out what that PID actually is:

```bash
ps -p <PID> -o pid,ppid,user,args
```

If the output shows `<defunct>` in the `ARGS` column, it's a zombie process. 

### 3. Kill the Parent Process of the Zombie

A zombie process cannot be killed directly. You must kill its **Parent PID (PPID)** to force the operating system to reap it.

From the `ps` output above, find the `PPID` and check what it is:
```bash
ps -p <PPID> -o pid,ppid,user,args
```

Once you identify the parent process (often a hung bash script or an older `openclaw` shell wrapper), terminate it forcefully:
```bash
kill -9 <PPID>
```

### 4. Clear the Stale Lockfile

Although the zombie process is gone, the lockfile it created might still be dangling on disk. Clear it gracefully using the OpenClaw CLI:

```bash
openclaw gateway stop
```

### 5. Restart the Gateway via LaunchAgent

Now that the old process tree is cleared and the lockfile is removed, bootstrap the service again to start it fresh:

```bash
launchctl bootstrap gui/$UID ~/Library/LaunchAgents/ai.openclaw.gateway.plist
```
*(Or use `openclaw gateway start` depending on how you prefer to manage the service).*

### 6. Verify Success

Check the standard log output to confirm it successfully bound to the port and logged in:

```bash
tail -n 20 ~/.openclaw/logs/gateway.log
```

You should see output similar to:
```text
[gateway] listening on ws://127.0.0.1:18789
[discord] logged in to discord as 123456789
```
