@echo off
echo Running scheduler fix... Please wait...
echo.
powershell.exe -ExecutionPolicy Bypass -File "FINAL_FIX_RUN_THIS.ps1" > fix_output.log 2>&1
echo.
echo Fix completed! Opening log file...
echo.
type fix_output.log
echo.
echo Log saved to: fix_output.log
echo.
pause

