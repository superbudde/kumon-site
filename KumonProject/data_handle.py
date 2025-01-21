from openpyxl import load_workbook
import pandas as pd


# Collects data from xlsx file (Student Database), turning it into a list
def data_collect(file_name, sheet_name):
    wb = load_workbook(file_name)
    ws = wb[sheet_name]
    wlist = list(ws.rows)
    sheet = []
    for i in range(len(wlist)):
        sheet.append(list(wlist[i]))
        for j in range(len(wlist[i])):
            sheet[i][j] = wlist[i][j].value
    return sheet


# Exports new data into an xlsx file (Student Logins)
def data_export(file_name, sheet_name, sheet):
    pd.set_option('display.max_colwidth', None)
    df = pd.DataFrame(sheet)
    # df.to_excel(file_name, sheet_name=sheet_name, index=False)

    with pd.ExcelWriter(file_name, engine='openpyxl', mode='a') as writer:
        try:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        except ValueError:
            writer.book.remove(writer.book[sheet_name])
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            # print("Sheet for this day already exists")
