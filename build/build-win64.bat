pyinstaller -F --clean ../main.py -p ../core/ExcelSerializer.py -p ../core/Utility -p ../core/MicroblogCrawler.py
ren dist\main.exe MicroblogCrawler.exe
pause