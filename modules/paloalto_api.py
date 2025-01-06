import requests
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':DES-CBC3-SHA'
requests.packages.urllib3.disable_warnings()
import xml.etree.ElementTree as ET
import pandas as pd
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
import time
import os
import datetime

from openpyxl import load_workbook
from openpyxl.styles import PatternFill

def apply_excel_style(file_name):
    """
        주어진 엑셀파일의 헤더에 연한 회색 배경을 적용하고,
        헤더의 너비를 자동으로 조절하되 최대 너비를 40으로 제한하는 함수.

        :param file_name: 처리할 엑셀파일의 이름
    """
    try:
        # load excel file
        workbook = load_workbook(file_name)
        worksheet = workbook.active

        # set range of header (first row is header)
        header_range = worksheet[1]

        fill = PatternFill(start_color='D3D3D3', end_color='D3D3D3', fill_type='solid')

        for cell in header_range:
            cell.fill = fill
            column_letter = cell.column_letter
            max_length = 0
            for cell in worksheet[column_letter]:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = (max_length + 2) * 1.2
            worksheet.column_dimensions[column_letter].width = min(40, adjusted_width)
        
        workbook.save(file_name)
    
    except Exception as e:
        print(f"An error occurred: {e}")

class PaloAltoAPI:
    def __init__(self, hostname, username, password):
        self.hostname = hostname
        self.base_url = f'https://{hostname}/api/'
        self.api_key = self.get_api_key(username, password)

    def save_dfs_to_excel(self, dfs, sheet_names, file_name):
        try:
            if not isinstance(dfs, list):
                dfs = [dfs]
            
            if not isinstance(sheet_names, list):
                sheet_names = [sheet_names]
            
            with pd.ExcelWriter(file_name) as writer:
                for df, sheet_name in zip(dfs, sheet_names):
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            apply_excel_style(file_name)
            return True
        except:
            return False
    
    def save_df_to_excel(self, df, df_name):
        current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        save_file = f"{current_date}_{self.hostname}_{df_name}.xlsx"
        if os.path.isfile(save_file):
            raise FileExistsError(f"File '{save_file}' already exists")
        
        with pd.ExcelWriter(save_file, engine='openpyxl') as writer:
            df.to_excel(wirter, sheet_name=df_name, index=False)
    
    def get_member(self, entry):
        try:
            result = [ member.text for member in entry ]
        except:
            result = []
        
        return result
    
    def list_to_string(self, list_data):
        return ','.join(str(s) for s in list_data)
    
    def get_api_data(self, parameter: dict, time_out: int = 10000):
        try:
            response = requests.get(self.base_url, params=parameter, verify=False, timeout=time_out)
            return response
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API 요청 중 요류 발생: {e}")
    
    def get_api_key(self, username:str, password: str):
        keygen_parameter = (
            ('type', 'keygen'),
            ('user', username),
            ('password', password)
        )

        try:
            response = self.get_api_data(keygen_parameter)
            key_value = ET.fromstring(response.text).find('./result/key')
            api_key = key_value.text
            
            return api_key
        
        except requests.exceptions.RequestException as e:
            raise ValueError(f"API 요청 중 오류 발생: {e}")
    
    def get_vsys_list(self):
        parameter = (
            ('key', self.api_key),
            ('type', 'config'),
            ('action', 'get'),
            ('xpath', '/config/devices/entry/vsys/entry'),
        )

        response = self.get_api_data(parameter)
        root = ET.fromstring(response.text).findall('./result/entry')
        vsys_list = []
        for vsys in root:
            vsys_list.append(vsys.attrib.get('name'))

        return vsys_list
    
    def get_config(self, config_type: str = 'running'):
        action = 'show' if config_type == 'running' else 'get'
        parameter = (
            ('key', self.api_key),
            ('type', 'config'),
            ('action', action),
            ('xpath', '/config')
        )

        response = self.get_api.data(parameter)

        return response.text
    
    def save_config(self, config_type: str = 'running'):
        current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
        config = self.get_config(config_type)
        with open(f'{current_date}_{self.hostname}_{config_type}_config.xml', mode='w', encoding='utf8') as file:
            file.write(config)
        
        return True