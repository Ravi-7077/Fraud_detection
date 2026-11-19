# setup_environment.ps1
# Script to install dependencies for the allowed System Python 3.14

$PythonExe = "C:\Program Files\Python314\python.exe"

if (-not (Test-Path $PythonExe)) {
    Write-Error "System Python 3.14 not found at $PythonExe. Please ensure Python 3.14 is installed."
    Exit 1
}

$TargetDir = Join-Path $PSScriptRoot ".venv_314"
$LibDir = Join-Path $TargetDir "Lib\site-packages"

Write-Host "Installing/Updating dependencies into $LibDir..."
& $PythonExe -m pip install --target $LibDir -r (Join-Path $PSScriptRoot "requirements_314.txt")

if ($LASTEXITCODE -eq 0) {
    Write-Host "Environment setup complete! Packages installed in $LibDir"
} else {
    Write-Error "Failed to install dependencies."
}
