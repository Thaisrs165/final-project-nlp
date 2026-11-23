# Deploying "The Unsure Hat" to Hugging Face Spaces

> ⚠️ **Checked 2026-11-23: Hugging Face now requires the paid PRO plan for Gradio (and Docker) Spaces.** Only static Spaces are free, and those can't run torch or our models. **Recommendation (not yet a team decision): don't deploy.** The app runs locally, and for the presentation it uses the temporary `GRADIO_SHARE=True` link (main README). The files and steps below still work if someone ever has a PRO account.

A Space gives the app a permanent public link (`https://huggingface.co/spaces/<user>/unsure-hat`). **Every step that needs an account or a login is done by a team member; never paste a token into a chat or a file.**

| File here | Becomes in the Space | Why |
|---|---|---|
| `space-card.md` | `README.md` | The YAML header tells Spaces: Gradio 6.31.0, Python 3.12, start `app/app.py`. |
| `requirements.txt` | `requirements.txt` | Only torch (CPU build), transformers and sentence-transformers. Gradio comes from `sdk_version`. |
| `prepare.sh` | (not copied) | Copies `sorter.py`, `app/` and only the 9 data files the app reads (tested 2026-11-23). |

## Steps

1. **Account (🛑 manual).** Sign up at https://huggingface.co/join and confirm your email.
2. **Create the Space (🛑 manual).** Go to https://huggingface.co/new-space and set:
   - Space name: `unsure-hat`;
   - SDK: **Gradio**, blank template;
   - Hardware: CPU basic (needs the PRO plan as of 2026-11);
   - Visibility: Public.

   Then click *Create Space*.
3. **Log in from the terminal (🛑 manual).** From the project folder:
   ```bash
   .venv/bin/hf auth login --add-to-git-credential
   ```
   It opens the browser to authorize, or asks for a token from https://huggingface.co/settings/tokens. The token must have **Write** permission. Type or paste it **only in your own terminal**.
4. **Clone the Space** next to the project folder. Replace `<user>` with your Hugging Face username:
   ```bash
   git clone https://huggingface.co/spaces/<user>/unsure-hat ../unsure-hat
   ```
5. **Copy the app into it:**
   ```bash
   bash space/prepare.sh ../unsure-hat
   ```
6. **Publish:**
   ```bash
   cd ../unsure-hat && git add -A && git commit -m "Deploy The Unsure Hat" && git push
   ```
7. **Wait for the build.** Open the Space page → *Logs*:
   - *Build* (installing torch) takes about 5–10 min;
   - *Container* then downloads the 3 models (~2 GB) on the first start.

   The status turns **Running** when it's ready.
8. **Test it**, then turn the URL into a QR code for the presentation and send the link to Esther for the report's Conclusion.

**To update later:** run step 5 again, then step 6.

## If something goes wrong
- **Build fails on `torch==2.15.0`:** delete the `--extra-index-url` line from the Space's `requirements.txt` and push again. It installs the bigger default torch, which also works.
- **Slow answers:** CPU basic has no GPU. The quiz grid (15 predictions) can take about 20–40 s there, against about 5 s on a Mac. That's fine for a demo. For the live presentation, the local app or the temporary `GRADIO_SHARE=True` link (see the main README) is faster.
- **"Sleeping" Space:** free Spaces sleep after about 48 h without visits. The first visit wakes it up, which takes about 1–2 min, so open it before presenting.
