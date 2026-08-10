# Start local Scoop PostgreSQL for Seagulls CRM
$ErrorActionPreference = "Stop"
$pgBin = Join-Path $env:USERPROFILE "scoop\apps\postgresql\current\bin"
$pgData = Join-Path $env:USERPROFILE "scoop\apps\postgresql\current\data"
$pgLog = Join-Path $env:USERPROFILE "scoop\apps\postgresql\current\logfile.log"

$env:Path = "$pgBin;" + $env:Path

$status = & pg_ctl -D $pgData status 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "PostgreSQL is already running."
} else {
    Write-Host "Starting PostgreSQL..."
    & pg_ctl -D $pgData -l $pgLog start
}

& pg_isready
Write-Host "Connection string:"
Write-Host "postgresql+psycopg2://seagulls:seagulls_crm_dev@127.0.0.1:5432/seagulls_crm"
