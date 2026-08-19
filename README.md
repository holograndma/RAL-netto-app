# Stipendio netto 2026 (Milano)

Estimator of take-home pay for a full-time, open-ended private-sector employee in Milan. Enter a RAL; the rest of the scenario is fixed (13 months, no dependents, no extra deductions).

This Origin copy is **not public**. Access is managed from the [Origin repo page](https://cursor.com/codebase/holograndma/RAL-netto-app).

Origin does not host a running app the way GitHub Pages does. The calculator is a static page in `public/`, so it can be deployed from this repo with [Vercel for Origin](https://vercel.com/docs/git/vercel-for-origin) (Settings → Apps on the Origin repo). Origin repositories are private and need a paid Vercel team, not Hobby.

After Vercel is connected, put the live URL here and in the repo README so people who can see the repo can open the app in one click.

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
