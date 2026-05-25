Set-Location $PSScriptRoot
Write-Host "Installing dependencies (if needed)..."
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 -m pip install -r requirements.txt
    py -3 main.py
} else {
    python -m pip install -r requirements.txt
    python main.py
}
