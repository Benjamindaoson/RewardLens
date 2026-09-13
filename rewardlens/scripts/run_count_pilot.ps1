$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Config = Join-Path $RepoRoot "configs\count_pilot_v1.json"
$Generate = Join-Path $RepoRoot "scripts\generate_count_pilot.py"
$Validate = Join-Path $RepoRoot "scripts\validate_count_pilot.py"

Write-Host "COUNT PILOT V1"
Write-Host "Repo: $RepoRoot"
Write-Host "Config: $Config"

python $Generate --config $Config
if ($LASTEXITCODE -ne 0) {
    Write-Error "generate_count_pilot.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

python $Validate --config $Config
if ($LASTEXITCODE -ne 0) {
    Write-Error "validate_count_pilot.py failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "COUNT_PILOT_V1_OK"
exit 0
