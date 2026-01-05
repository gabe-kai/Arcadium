# Run CI/CD tests locally
# This script simulates the GitHub Actions CI/CD workflow locally

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running CI/CD Tests Locally" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Set environment variables to match CI
$env:FLASK_ENV = "testing"
$env:TEST_DATABASE_URL = "postgresql://postgres:Le555ecure@localhost:5432/arcadium_testing_wiki"
$env:arcadium_user = "postgres"
$env:arcadium_pass = "Le555ecure"
$env:DB_HOST = "localhost"
$env:DB_PORT = "5432"

Write-Host "Environment Variables Set:" -ForegroundColor Yellow
Write-Host "  FLASK_ENV = $env:FLASK_ENV"
Write-Host "  TEST_DATABASE_URL = $env:TEST_DATABASE_URL"
Write-Host "  arcadium_user = $env:arcadium_user"
Write-Host "  DB_HOST = $env:DB_HOST"
Write-Host "  DB_PORT = $env:DB_PORT"
Write-Host ""

# Check if pre-commit should be run
$runPreCommit = $args -contains "--pre-commit" -or $args -contains "-p"

if ($runPreCommit) {
    Write-Host "Running pre-commit checks..." -ForegroundColor Yellow
    pre-commit run --all-files
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Pre-commit checks failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host ""
}

# Run the unified test runner (same as CI)
Write-Host "Running unified backend tests..." -ForegroundColor Yellow
Write-Host ""

$outputFile = "test-output-ci.txt"
python scripts/run-tests.py all 2>&1 | Tee-Object -FilePath $outputFile

$testExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Execution Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($testExitCode -eq 0) {
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed (exit code: $testExitCode)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Full test output saved to: $outputFile" -ForegroundColor Yellow
Write-Host "Test logs saved to: logs/tests/" -ForegroundColor Yellow

exit $testExitCode
