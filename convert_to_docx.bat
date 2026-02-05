@echo off
REM Simple batch script to convert Markdown to DOCX using Pandoc

echo Converting blog_post.md to DOCX...

REM Try to find and use pandoc
where pandoc >nul 2>&1
if %errorlevel% equ 0 (
    echo Found pandoc in PATH
    pandoc blog_post.md -o blog_post.docx --standalone
) else (
    echo Pandoc not in PATH, trying common installation locations...
    
    if exist "C:\Program Files\Pandoc\pandoc.exe" (
        "C:\Program Files\Pandoc\pandoc.exe" blog_post.md -o blog_post.docx --standalone
    ) else if exist "C:\Users\%USERNAME%\AppData\Local\Pandoc\pandoc.exe" (
        "C:\Users\%USERNAME%\AppData\Local\Pandoc\pandoc.exe" blog_post.md -o blog_post.docx --standalone
    ) else (
        echo ERROR: Could not find pandoc. Please restart your terminal or add Pandoc to PATH.
        pause
        exit /b 1
    )
)

if exist blog_post.docx (
    echo.
    echo ✅ SUCCESS! Created blog_post.docx
    echo.
    echo File location: %CD%\blog_post.docx
    echo.
) else (
    echo.
    echo ❌ FAILED: Could not create DOCX file
    echo.
)

pause
