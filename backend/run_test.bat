@echo off
REM Quick test script for Windows
REM Usage: 
REM   1. Double-click this file to run with default path
REM   2. Or drag and drop a PDF file/folder onto this file
REM   3. Or run from command line: run_test.bat [path_to_pdf_or_folder]

echo ========================================
echo Legal Contract Analyzer - Test Script
echo ========================================
echo.

REM Check if path provided as argument
if "%~1"=="" (
    REM No argument, use default path
    set TEST_PATH="C:\Users\92506\Desktop\4595826\CUAD_v1\full_contract_pdf\Part_I\Affiliate_Agreements"
    echo Using default path: %TEST_PATH%
) else (
    REM Use provided path
    set TEST_PATH="%~1"
    echo Using provided path: %TEST_PATH%
)

echo.
echo Starting tests...
echo.

REM Run the test script
python test_workflow.py %TEST_PATH%

echo.
echo ========================================
echo Tests completed!
echo ========================================
pause

