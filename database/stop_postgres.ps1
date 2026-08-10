# Stop local Scoop PostgreSQL
$ErrorActionPreference = "Stop"
$pgBin = Join-Path $env:USERPROFILE "scoop\apps\postgresql\current\bin"
$pgData = Join-Path $env:USERPROFILE "scoop\apps\postgresql\current\data"
$env:Path = "$pgBin;" + $env:Path
& pg_ctl -D $pgData stop
