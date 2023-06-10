pyinstaller -F --clean ../main.py -p ../core/ExcelSerializer.py -p ../core/Utility -p ../core/MicroblogCrawler.py

if exist dist\MicroblogCrawler.exe (
    del dist\MicroblogCrawler.exe
)
ren dist\main.exe MicroblogCrawler.exe
pause