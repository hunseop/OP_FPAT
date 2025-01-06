import pandas as pd
pd.options.mode.chained_assignment = None
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, PatternFill, Font
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import re
from datetime import datetime, timedelta
import os

COLUMNS = [
    'Rule Name', 'Source', 'User', 'Destination', 'Service', 'Application', 'Description',
    'REQUEST_ID', 'REQUEST_START_DATE', 'REQUEST_END_DATE', 'TITLE', 'REQUESTER_ID',
    'REQUESTER_EMAIL', 'REQUESTER_NAME', 'REQUESTER_DEPT', 'WRITER_PERSON_ID', 'WRITE_PERSON_EMAIL',
    'WRITE_PERSON_NAME', 'WRITE_PERSON_DEPT', 'APPROVAL_PERSON_ID', 'APPROVAL_PERSON_EMAIL',
    'APPROVAL_PERSON_NAME', 'APPROVAL_PERSON_DEPT_NAME'
]

COLUMNS_NO_HISTORY = [
    'Rule Name', 'Source', 'User', 'Destination', 'Service', 'Application', 'Description'
]

DATE_COLUMNS = ['REQUEST_START_DATE', 'REQUEST_END_DATE']

TRANSLATED_COLUMNS = {
    'REQUEST_ID': '신청번호',
    ### skiped
}

except_list = [
    'test',
    'sample',
]

def update_version(filename: str, final_version: bool = False) -> str:
    base_name, ext = filename.rsplit('.', 1)

    match = re.search(r'_v(\d+)$', base_name)
    final_match = re.search(r'_vf$', base_name)

    if final_match:
        return filename
    
    if final_version:
        if match:
            new_base_name = re.sub(r'_v\d+$', '_vf', base_name)
        else:
            new_base_name = f"{base_name}_vf"
    else:
        if match:
            version = int(match.group(1))
            new_version = version + 1
            new_base_name = re.sub(r'_v\d+$', f'_v{new_version}', base_name)
        else:
            new_base_name = f"{base_name}_v1"
    
    new_filename = f"{new_base_name}.{ext}"
    return new_filename

def select_xlsx_files(extension='.xlsx'):
    file_list = [file for file in os.listdir() if file.endswith(extension)]
    if not file_list:
        print("no excel file")
        return None
    
    for i ,file in enumerate(file_list, start=1):
        print(f"{i}. {file}")
    
    while True:
        choice = input("input file number (exit: 0) ")
        if choice.isdigit():
            choice = int(choice)
            if choice == 0:
                print('exit the program')
                return None
            elif 1 <= choice <= len(file_list):
                return file_list[choice -1]
        print('Invalid number. try again.')
    
def save_to_excel(df, type, file_name):
    wb = load_workbook(file_name)
    sheet = wb[type]

    sheet.insert_rows(1)
    sheet['A1'] = '="대상 정책 수: "&COUNTA(B:B)-1'

    sheet['A1'].font = Font(bold=True)

    for col in range(1, 8):
        cell = sheet.cell(row=2, column=col)
        cell.alignment = Alignment(horizontal='center')
        cell.fill = PatternFill(start_color='E0E0E0', end_color='E0E0E0', fill_type='solid')
    
    if type != '이력없음_미사용정책':
        for col in range(8, 24):
            cell = sheet.cell(row=2, column=col)
            cell.fill = PatternFill(start_color='ccffff', end_color='ccffff', fill_type='solid')
    
    wb.save(file_name)

def remove_extension(filename):
    return os.path.splitext(filename)[0]

# 1. parsing request id from description
def parse_request_type():
    def convert_to_date(date_str):
        try:
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            return date_str
    
    def parse_request_info(rulename, description):
        data_dict = {
            "Request Type": "Unknown",
            "Request ID": None,
            "Ruleset ID": None,
            "MIS ID": None,
            "Request User": None,
            "Start Date": convert_to_date('19000101'),
            "End Date": convert_to_date('19000101'),
        }

        if pd.isnull(description):
            return data_dict
        
        # initial pattern
        pattern_3 = re.compile("MASKED")
        pattern_1_rulename = re.compile("MASKED")
        pattern_1_user = r'MASKED'
        rulename_1_rulename = r'MASKED'
        rulename_1_date = r'MASKED'

        # matched
        match_3 = pattern_3.match(description)
        name_match = pattern_1_rulename.match(str(rulename))
        user_match = re.search(pattern_1_user, description)
        desc_match = re.search(rulename_1, description)
        date_match = re.search(rulename_1_date, description)

        if match_3:
            data_dict = {
                "Request Type": None,
                "Request ID": match_3.group(5),
                "Ruleset ID": match_3.group(1),
                "MIS ID": match_3.group(6) if match_3.group(6) else None,
                "Request User": match_3.group(4),
                "Start Date": convert_to_date(match_3.group(2)),
                "End Date": convert_to_date(match_3.group(3)),
            }
            
            type_code = data_dict["Request ID"][:1]
            if type_code == "P":
                data_dict["Request Type"] = "GROUP"
            elif type_code == "F":
                data_dict["Request Type"] = "NORMAL"
            elif type_code == "S":
                data_dict["Request Type"] = "SERVER"
            elif type_code == "M":
                data_dict["Request Type"] = "PAM"
            else:
                data_dict["Request Type"] = "Unknown"
        
        if name_match:
            data_dict['Request Type'] = "OLD"
            data_dict['Request ID'] = name_match.group(1)
            if user_match:
                data_dict['Request User'] = user_match.group(1).replace("*ACL*", "")
            if date_match:
                data_dict['Start Date'] = convert_to_date(date_match.group().split("~")[0])
                data_dict['End Date'] = convert_to_date(date_match.group().split("~")[1])
        
        if desc_match:
            date = description.split(';')[0]
            start_date = date.split('~')[0].replace('[', '').replace('-', '')
            end_date = date.split('~')[1].replace(']', '').replace('-', '')

            date_dict = {
                "Request Type": "OLD",
                "Request ID": desc_match.group(1).split('-')[1],
                "Ruleset ID": None,
                "MIS ID": None,
                "Request User": user_match.group(1).replace("*ACL*", "") if user_match else None,
                "Start Date": convert_to_date(start_date),
                "End Date": convert_to_date(end_date),
            }
        
        return data_dict
    
    file_name = select_xlsx_files()
    df = pd.read_excel(file_name)

    for index, row in df.iterrows():
        result = parse_request_info(row['Rule Name'], row['Description'])
        for key, value in result.items():
            df.at[index, key] = value
    
    df.to_excel(update_version(file_name), index=False)