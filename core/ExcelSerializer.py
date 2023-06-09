from .Utility import *
import xlwings as Excel
import sys

# Excel Serializer
class ExcelSerializer:
    def __init__(self) -> None:
        try:
            self.excelApp = Excel.App(False, False)
        except:
            Utility.PrintLog("Excel is not installed properly on this computer! Program exiting...", Colors.red)
            sys.exit(-1)

        self.excelApp.display_alerts = False    
        self.excelApp.screen_updating = False

        self.excelBook = self.excelApp.books.add()
        self.excelSheet = self.excelBook.sheets.add()

        self.excelSheet.range("A:F").api.NumberFormat ="@"
        self.excelSheet.range("A1:F1").api.Merge()
        self.excelSheet.range(1, 1).row_height = 30
        self.excelSheet.range("A:E").column_width = 12
        self.excelSheet.range("F:F").column_width = 120
        self.excelSheet.range(1, 1).api.HorizontalAlignment = -4131

        headers = ["Type", "Like Count", "User ID", "User Name", "Post Time", "Content"]
        self.excelSheet.range("A2").value = headers

        self.currentRow = 3

    def WriteMainContent(self, content: str) -> None:
        self.excelSheet.range("A1").value = content

    def WriteLine(self, values: list) -> None:
        self.excelSheet.range("A" + str(self.currentRow)).value = values
        self.currentRow += 1

    def Save(self, folderName: str, fileName: str) -> None:
        self.excelBook.save(folderName + fileName)

    def Close(self) -> None:
        self.excelBook.close()
