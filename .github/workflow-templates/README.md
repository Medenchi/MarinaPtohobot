# Workflow Templates

These are GitHub Actions workflows for this project. Devin's OAuth App
cannot push workflow files directly, so they live here. To enable them:

1. Copy the `.yml` files from this directory to `.github/workflows/`
2. Commit and push (via web UI or with a PAT that has `workflow` scope)
3. In repo Settings → Pages: set Source to "GitHub Actions"
4. In repo Settings → Secrets and variables → Actions:
   - **Variables**: `VITE_SUPABASE_URL`, `VITE_API_URL`
   - **Secret**: `VITE_SUPABASE_ANON_KEY`

After that, `frontend.yml` will auto-deploy `frontend/` to GitHub Pages
(custom domain `marina.denchy.cyou`) on every push to `main`.
