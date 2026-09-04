@echo off
chcp 65001 >nul
echo.
echo  Q1 Browser - merge portable Windows package
echo =============================================
echo.
echo  Combining the parts into Q1Browser-Windows-Portable.zip...
copy /b "%~dp0Q1Browser-Windows-Portable.zip.000"+"%~dp0Q1Browser-Windows-Portable.zip.001"+"%~dp0Q1Browser-Windows-Portable.zip.002" "%~dp0Q1Browser-Windows-Portable.zip" >nul
if errorlevel 1 (
  echo.
  echo  ERROR: merge failed. Please download all three parts again.
  pause
  exit /b 1
)
echo.
echo  Done! Now extract Q1Browser-Windows-Portable.zip.
echo  Then double-click Q1Browser.exe inside the extracted folder.
echo.
pause
