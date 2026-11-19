$PythonExe = "C:\Program Files\Python314\python.exe"
$Venv314 = "$PSScriptRoot\.venv_314"

if (Test-Path $PythonExe) {
    Write-Host "Application Control Policy workaround: Using system Python 3.14 with target package directory."
    
    # Check if packages are installed, if not, run setup
    $LibDir = "$Venv314\Lib\site-packages"
    if (-not (Test-Path $LibDir)) {
        Write-Host "Dependencies not found in $LibDir. Running setup_environment.ps1 first..."
        & "$PSScriptRoot\setup_environment.ps1"
    }

    # Set PYTHONPATH to include the target library and the parent directory of the package
    $env:PYTHONPATH = "$Venv314\Lib\site-packages;$PSScriptRoot\.."

    # Start the FastAPI app using the allowed python executable (unbuffered)
    & $PythonExe -u -m uvicorn fraud_detection.api.main:app --host 127.0.0.1 --port 8000 $args
} else {
    # Fallback to standard virtualenv running
    Write-Host "Using standard virtual environment..."
    $env:PYTHONPATH = "$PSScriptRoot\.."
    $env:VIRTUAL_ENV = "$PSScriptRoot\.venv"
    $path_elements = $env:PATH -split ';'
    $filtered_elements = $path_elements | Where-Object { $_ -notlike "*\.venv\Scripts*" -and $_ -notlike "*\.venv/Scripts*" }
    $env:PATH = ("$PSScriptRoot\.venv\Scripts" + ";" + ($filtered_elements -join ';'))

    uvicorn fraud_detection.api.main:app --host 127.0.0.1 --port 8000 $args
}
