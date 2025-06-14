import csv
from docx import Document
import pandas as pd

# Mở file Word
doc = Document('Chatbot24-36.docx')

# Mở file CSV để ghi dữ liệu
with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)

    # Duyệt qua tất cả các bảng trong tài liệu
    for table in doc.tables:
        for row in table.rows:
            # Duyệt qua các ô trong mỗi hàng và lấy dữ liệu
            row_data = [cell.text.strip() for cell in row.cells]
            # Ghi dữ liệu vào file CSV
            writer.writerow(row_data)


final_file = '24to36moths.txt'
data = pd.read_csv('output.csv')
data = data.dropna()
data['NỘI DUNG'] = data['NỘI DUNG'].str.replace('\n\n', '\n')
with open(final_file, 'a', encoding='utf-8') as file:
    for index, row in data.iterrows():
        file.write(f"Câu hỏi: {row['CÂU HỎI']}\nTrả lời: {row['NỘI DUNG']}\n\n")