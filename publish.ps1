$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
try {
    python scripts/upload_images.py
    if ($LASTEXITCODE -ne 0) { throw 'Image upload failed. Blog was not published. Check Python and image paths.' }
    git add -- docs assets _layouts _config.yml index.html .github scripts .gitignore publish.cmd publish.ps1 README.md
    if ($LASTEXITCODE -ne 0) { throw 'Git add failed.' }
    git diff --cached --quiet
    $diffResult = $LASTEXITCODE
    if ($diffResult -eq 1) {
        git commit -m ("Publish blog " + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))
        if ($LASTEXITCODE -ne 0) { throw 'Git commit failed.' }
    } elseif ($diffResult -ne 0) { throw 'Git diff failed.' }
    git push origin main
    if ($LASTEXITCODE -ne 0) { throw 'Push failed. Check network, GitHub login, or remote changes.' }
    Write-Host 'Uploaded. GitHub Actions is building your blog:' -ForegroundColor Green
    Write-Host 'https://github.com/Limanman507/Limanman507.github.io/actions'
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
