# PowerShell script for running tests
# Usage: .\run_test.ps1 [path_to_pdf_or_folder]

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Legal Contract Analyzer - Test Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if path provided as argument
if ($args.Count -eq 0) {
    # No argument, use default path
    $TEST_PATH = "C:\Users\92506\Desktop\4595826\CUAD_v1\full_contract_pdf\Part_I\Affiliate_Agreements"
    Write-Host "Using default path: $TEST_PATH" -ForegroundColor Yellow
} else {
    # Use provided path
    $TEST_PATH = $args[0]
    Write-Host "Using provided path: $TEST_PATH" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Starting tests..." -ForegroundColor Green
Write-Host ""

# Run the test script
python test_workflow.py $TEST_PATH

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Tests completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

