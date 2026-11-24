# SERA one-click launcher (Windows / PowerShell 5.1+)
# Starts: project-local PostgreSQL (port 55432) -> migrations -> FastAPI backend (8000) -> Vite frontend (5173)
# then opens the browser. Safe to run repeatedly; it reuses whatever is already running.

$ErrorActionPreference = "Continue"   # native tools write progress to stderr; we check exit codes instead
$Root     = Split-Path -Parent $MyInvocation.MyCommand.Path
$Backend  = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$PgData   = Join-Path $Root ".localdb\pgdata"
$PgLog    = Join-Path $Root ".localdb\postgres.log"
$PgPort   = 55432
$Host.UI.RawUI.WindowTitle = "SERA launcher"

function Say($msg, $color = "Cyan") { Write-Host "[SERA] $msg" -ForegroundColor $color }
function Fail($msg) { Write-Host "[SERA] $msg" -ForegroundColor Red; Read-Host "Press Enter to close"; exit 1 }
function PortOpen($port) {
  try { $c = New-Object Net.Sockets.TcpClient; $c.Connect("127.0.0.1", $port); $c.Close(); return $true } catch { return $false }
}
function WaitFor($url, $seconds) {
  for ($i = 0; $i -lt $seconds; $i++) {
    try { Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 $url | Out-Null; return $true } catch { Start-Sleep 1 }
  }
  return $false
}

Write-Host ""
Write-Host "  SERA - Securities Engine for Regulatory Action" -ForegroundColor Green
Write-Host "  Local mode: PostgreSQL + FastAPI + React, nothing deployed" -ForegroundColor DarkGray
Write-Host ""

# ---------- 1. PostgreSQL --------------------------------------------------
$pgBin = $null
$cmd = Get-Command pg_ctl.exe -ErrorAction SilentlyContinue
if ($cmd) { $pgBin = Split-Path $cmd.Source }
if (-not $pgBin) {
  $cand = Get-ChildItem "C:\Program Files\PostgreSQL\*\bin\pg_ctl.exe" -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1
  if ($cand) { $pgBin = Split-Path $cand.FullName }
}
if (-not $pgBin) { Fail "PostgreSQL binaries not found. Install PostgreSQL 15+ from postgresql.org and re-run." }

if (-not (Test-Path (Join-Path $PgData "PG_VERSION"))) {
  Say "Creating local PostgreSQL cluster in .localdb (user sera / pw sera)..."
  New-Item -ItemType Directory -Force (Split-Path $PgData) | Out-Null
  $pw = Join-Path $env:TEMP "sera_pg_pw.txt"
  Set-Content -Path $pw -Value "sera" -NoNewline -Encoding ascii
  & "$pgBin\initdb.exe" -D $PgData -U sera --pwfile=$pw -A scram-sha-256 -E UTF8 --locale=C | Out-Null
  Remove-Item $pw -Force
}
if (-not (PortOpen $PgPort)) {
  Say "Starting PostgreSQL on port $PgPort..."
  Start-Process -FilePath "$pgBin\pg_ctl.exe" -ArgumentList @("-D", "`"$PgData`"", "-o", "`"-p $PgPort`"", "-l", "`"$PgLog`"", "start", "-w") -WindowStyle Hidden -Wait
  Start-Sleep 1
  if (-not (PortOpen $PgPort)) { Fail "PostgreSQL did not start. See $PgLog" }
} else { Say "PostgreSQL already running on $PgPort" "DarkGray" }
$env:PGPASSWORD = "sera"
$exists = & "$pgBin\psql.exe" -h 127.0.0.1 -p $PgPort -U sera -d postgres -tAc "select 1 from pg_database where datname='sera'"
if ("$exists".Trim() -ne "1") {
  Say "Creating database 'sera'..."
  & "$pgBin\psql.exe" -h 127.0.0.1 -p $PgPort -U sera -d postgres -c "create database sera" | Out-Null
}

# ---------- 2. Backend -----------------------------------------------------
$py = Join-Path $Backend ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  Say "Creating Python 3.12 virtual environment (first run only)..."
  Push-Location $Backend
  try { & py -3.12 -m venv .venv } catch { & python -m venv .venv }
  Pop-Location
  if (-not (Test-Path $py)) { Fail "Could not create a Python venv. Install Python 3.12." }
}
$marker = Join-Path $Backend ".venv\.sera-deps"
$req = Join-Path $Backend "requirements.txt"
if (-not (Test-Path $marker) -or ((Get-Item $req).LastWriteTime -gt (Get-Item $marker).LastWriteTime)) {
  Say "Installing backend dependencies..."
  & $py -m pip install -q -r $req
  if ($LASTEXITCODE -ne 0) { Fail "pip install failed" }
  New-Item -ItemType File -Force $marker | Out-Null
}
$envFile = Join-Path $Backend ".env"
if (-not (Test-Path $envFile)) {
  Say "Creating backend/.env"
  @(
    "DATABASE_URL=postgresql+asyncpg://sera:sera@127.0.0.1:$PgPort/sera",
    "EMAIL_ENABLED=false",
    "FRONTEND_URL=http://localhost:5173",
    "ANTHROPIC_API_KEY=",
    "GROQ_API_KEY="
  ) | Set-Content -Path $envFile -Encoding utf8
} elseif (-not (Select-String -Path $envFile -Pattern "^DATABASE_URL=" -Quiet)) {
  Add-Content -Path $envFile -Value "`nDATABASE_URL=postgresql+asyncpg://sera:sera@127.0.0.1:$PgPort/sera"
}
Say "Applying database migrations..."
Push-Location $Backend
$env:PYTHONUTF8 = "1"
& $py -m alembic upgrade head *> (Join-Path $Root ".localdb\migrate.log")
if ($LASTEXITCODE -ne 0) { Pop-Location; Fail "Alembic migration failed (run 'python -m alembic upgrade head' in backend for details)" }
Pop-Location

if (-not (PortOpen 8000)) {
  Say "Starting backend on http://127.0.0.1:8000 ..."
  Start-Process -FilePath "powershell.exe" -WorkingDirectory $Backend -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='SERA backend (close to stop)'; `$env:PYTHONUTF8='1'; & '$py' -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
  )
} else { Say "Backend already running on 8000" "DarkGray" }

# ---------- 3. Frontend ----------------------------------------------------
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { Fail "Node.js/npm not found. Install Node 20+." }
if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
  Say "Installing frontend dependencies (first run only, a few minutes)..."
  Push-Location $Frontend; & npm install --no-audit --no-fund; Pop-Location
}
if (-not (PortOpen 5173)) {
  Say "Starting frontend on http://localhost:5173 ..."
  Start-Process -FilePath "powershell.exe" -WorkingDirectory $Frontend -ArgumentList @(
    "-NoExit", "-Command",
    "`$host.UI.RawUI.WindowTitle='SERA frontend (close to stop)'; npx vite dev --port 5173 --strictPort"
  )
} else { Say "Frontend already running on 5173" "DarkGray" }

# ---------- 4. Open ----------------------------------------------------------
Say "Waiting for services..."
if (-not (WaitFor "http://127.0.0.1:8000/api/v2/meta" 60)) { Fail "Backend did not come up - check the 'SERA backend' window." }
if (-not (WaitFor "http://localhost:5173/" 90)) { Fail "Frontend did not come up - check the 'SERA frontend' window." }
Say "SERA is running -> http://localhost:5173" "Green"
Start-Process "http://localhost:5173"
Start-Sleep 3
