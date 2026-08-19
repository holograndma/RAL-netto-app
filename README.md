# Stipendio netto 2026 (Milano)

Estimator of take-home pay for a full-time, open-ended private-sector employee in Milan. Enter a RAL; the rest of the scenario is fixed (13 months, no dependents, no extra deductions).

This Origin copy is **not public**. Access is managed from the [Origin repo page](https://cursor.com/codebase/holograndma/RAL-netto-app).

Origin does not host a running app the way GitHub Pages does. The calculator is a static page in `public/`. Deploy it with [Vercel for Origin](https://vercel.com/docs/git/vercel-for-origin) from a **paid Vercel team** (Hobby cannot deploy private Origin repos).

If you click **Reinstall** on the Vercel app in Origin, the old Vercel project loses Git access and can sit on a loading screen. Reconnect instead of waiting:

1. Origin: [Codebase Apps](https://cursor.com/codebase/settings/apps) — Vercel should show as installed (install once; do not reinstall again).
2. Vercel: [New Project](https://vercel.com/new) → **Continue with Origin** → select `holograndma/RAL-netto-app`.
3. Framework preset **Other**, output directory `public`, build command empty.

`vercel.json` already sets those so Vercel does not treat `app.py` as Flask.

## Open the code

[Open in Cursor](cursor://vscode.git/clone?url=https://origin.cursor.com/holograndma/RAL-netto-app.git)

Then **Run and Debug → View stipendio netto** (or `F5`), or:

```bash
./run.sh
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000). You can also open `public/index.html` directly in a browser.

CLI:

```bash
python italy_net_income.py 35000
```
