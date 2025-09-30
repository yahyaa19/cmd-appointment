param(
    [switch]$Help,
    [ValidateSet('test','perf','clean')]
    [string]$Task = 'test',
    [int]$Users = 200,
    [int]$Rounds = 1,
    [int]$Batch = 1000
)

function Show-Help {
    Write-Host "Usage: scripts/test.ps1 [-Task test|perf|clean] [-Users <int>] [-Rounds <int>] [-Batch <int>]" -ForegroundColor Cyan
    Write-Host "" 
    Write-Host "Tasks:" -ForegroundColor Yellow
    Write-Host "  test  - Run non-performance tests (skips @performance)"
    Write-Host "  perf  - Run performance tests (configurable via Users/Rounds/Batch)"
    Write-Host "  clean - Reset test DB schema via Alembic (uses TEST_DATABASE_URL)"
    Write-Host "" 
    Write-Host "Examples:" -ForegroundColor Yellow
    Write-Host "  # Non-performance suite" 
    Write-Host "  pwsh scripts/test.ps1 -Task test"
    Write-Host "" 
    Write-Host "  # Performance: 6000 users in 2 rounds, batch of 1000" 
    Write-Host "  pwsh scripts/test.ps1 -Task perf -Users 6000 -Rounds 2 -Batch 1000"
    Write-Host "" 
    Write-Host "  # Clean DB (alembic downgrade/upgrade)" 
    Write-Host "  $env:TEST_DATABASE_URL=\"postgresql://postgres:PASS@localhost:5432/appointment_test_db\"; pwsh scripts/test.ps1 -Task clean"
}

if ($Help) { Show-Help; exit 0 }

switch ($Task) {
  'test' {
    # Ensure tests start with clean tables per-test
    Remove-Item Env:TEST_DB_PRESERVE -ErrorAction SilentlyContinue
    pytest -m "not performance" -q
  }
  'perf' {
    # Configure perf env vars
    $env:PERF_USERS = "$Users"
    $env:PERF_ROUNDS = "$Rounds"
    $env:PERF_BATCH = "$Batch"
    # Avoid preserving data during perf runs by default
    Remove-Item Env:TEST_DB_PRESERVE -ErrorAction SilentlyContinue
    pytest -q -k "test_concurrent_creates_and_lists or test_stress_create_list_delete_cycles"
  }
  'clean' {
    if (-not $env:TEST_DATABASE_URL) {
      Write-Error "TEST_DATABASE_URL is not set. Please set it to your Postgres URL before running clean."
      exit 1
    }
    Write-Host "Resetting schema via Alembic on $($env:TEST_DATABASE_URL)" -ForegroundColor Yellow
    alembic -x sqlalchemy.url=$env:TEST_DATABASE_URL downgrade base
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    alembic -x sqlalchemy.url=$env:TEST_DATABASE_URL upgrade head
  }
  default { Show-Help }
}
