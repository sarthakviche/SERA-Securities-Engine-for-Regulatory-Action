# Stops SERA: frontend (5173), backend (8000) and the project-local PostgreSQL cluster.
$Root   = Split-Path -Parent $MyInvocation.MyCommand.Path
$PgData = Join-Path $Root ".localdb\pgdata"

foreach ($port in 5173, 8000) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  foreach ($c in $conns) {
    try { Stop-Process -Id $c.OwningProcess -Force -ErrorAction Stop; Write-Host "[SERA] stopped process on port $port" } catch {}
  }
}
$pgCtl = (Get-Command pg_ctl.exe -ErrorAction SilentlyContinue).Source
if (-not $pgCtl) { $pgCtl = (Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_ctl.exe" -ErrorAction SilentlyContinue | Select-Object -First 1).FullName }
if ($pgCtl -and (Test-Path $PgData)) { & $pgCtl -D $PgData stop -m fast | Out-Null; Write-Host "[SERA] PostgreSQL stopped" }
Start-Sleep 2
