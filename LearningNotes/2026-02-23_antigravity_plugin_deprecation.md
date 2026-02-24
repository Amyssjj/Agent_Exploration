# The "Antigravity" Deprecation and Migration {2026-02-23}

*Created at: 2026-02-23*


## 1. The Problem

Users relying on the `google-antigravity-auth` plugin within OpenClaw are experiencing a `"plugin not found: google-antigravity-auth"` config validation error. This prevents the OpenClaw service from starting or successfully loading its extensions when configured to use the Antigravity provider.

## 2. Investigation & Insights

The failure is caused by an intentional architectural change in the OpenClaw codebase. As of commit `382fe8009`, the core team completely removed the `google-antigravity` provider support and deleted its bundled auth plugin. 

### Why was it removed?

The `google-antigravity` plugin was acting as a proxy to run Anthropic Claude models (like Opus and Sonnet) through Google's internal Cloud Code Assist API. This required maintaining complex translation layers between Anthropic's API format and Google's API format. 

In the week leading up to its removal, this architecture proved unmaintainable due to fundamental differences:

- **JSON Schema Strictness:** Anthropic's advanced tool calling relies on JSON schemas with complex variants (`anyOf`/`oneOf`). Google's API strictly rejected these schemas, leading to constant "JSON schema is invalid" 400 errors for users trying to use tools like `web_search`.
- **Reasoning/Thinking Blocks:** Anthropic Claude 3.5+ returns reasoning processes in dedicated `thinking` blocks. Google's routing layer expects these blocks to carry cryptographic signatures, which unsigned Anthropic responses lacked. The team had to write brittle sanitizers to either fake signatures or downgrade thinking blocks to plain text to prevent the API from dropping the requests.

Rather than continuing to patch endless translation bugs between two competing architectures, the maintainers deprecated the Antigravity provider entirely.

## 3. Impact on the User

Any existing configuration referencing `google-antigravity-auth` in the `plugins.entries` or `plugins.allow` arrays will instantly fail on startup. Furthermore, any agent defaults or profile overrides specifying model IDs with the `google-antigravity/` prefix are now invalid.

Users must migrate to the officially supported plugins for their target models. For native Google Gemini capabilities, the new standard is the `google-gemini-cli` provider.

## 4. Migration Method

To restore functionality and migrate off the deprecated plugin:

1. **Update `openclaw.json` Plugins:**
   Remove the `google-antigravity-auth` entry and replace it with `google-gemini-cli-auth`.
   ```json5
   {
     "plugins": {
       "allow": ["google-gemini-cli-auth"],
       "entries": {
         "google-gemini-cli-auth": {}
       }
     }
   }
   ```

2. **Update Model References:**
   Change any default models in your configuration from the `google-antigravity/*` prefix to the new `google-gemini-cli/*` prefix (or fallback to basic `google/*` API key configs if preferred).
   ```json5
   {
     "agents": {
       "defaults": {
         "model": {
           "primary": "google-gemini-cli/gemini-1.5-pro-latest"
         }
       }
     }
   }
   ```

3. **Re-Authenticate via CLI:**
   Run the CLI commands to initialize the new OAuth session profile on your local machine:
   ```bash
   openclaw plugins enable google-gemini-cli-auth
   openclaw models auth login --provider google-gemini-cli --set-default
   ```
