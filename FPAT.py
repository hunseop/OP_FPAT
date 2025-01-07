#!/usr/bin/python

import argparse
import logging
import os
import time
import sys
from modules import secui_mf2, secui_ngf, paloalto_api, analysis_module, deletion_process

# Load Configuration
os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYWORD_DIC = f'{BASE_DIR}'

def setup_logging(hostname):
    log_format = "%{asctime}s %{levelname}s %{hostname}s %{message}s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    class HostnameFilter(logging.Filter):
        def filter(self, record):
            record.hostname = hostname
            return True
    logging.getLogger().addFilter(HostnameFilter)

def paloalto_command(args):
    try:
        hostname_list = args.ip.split(',')
        usesrname = args.username
        password = args.password
    except:
        logging.error("Invalid Arguments")
    
    for hostname in hostname_list:
        setup_logging(hostname)
        api = paloalto_api.PaloAltoAPI(hostname, usesrname, password)
        fw_name = api.get_system_info()['hostname'].iloc[0]

        if args.feature == 'show':
            if args.show_command == 'info':
                try:
                    logging.info(f"Starting '{args.feature} {args.show_command}'")
                    info = api.get_system_info()
                    print(info)
                    logging.info(f"Completed '{args.feature} {args.show_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.show_command}': {e}")

            elif args.show_command == 'thresholds':
                try:
                    logging.info(f"Starting '{args.feature} {args.show_command}'")
                    thresholds = api.get_system_state()
                    print(thresholds)
                    logging.info(f"Completed '{args.feature} {args.show_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.show_command}': {e}")    
        
        elif args.feature == 'export':
            if args.export_command == 'config':
                logging.info(f"Starting '{args.feature} {args.export_command}'")
                try:
                    api.save_config(args.type)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")
            
            elif args.export_command == 'rules':
                try:
                    logging.info(f"Starting '{args.feature} {args.export_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{fw_name}_{args.type}_{args.export_command}.xlsx'
                    rule_df = api.export_security_rules(args.type)
                    api.save_dfs_to_excel(rule_df, 'rules', file_name)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")

            elif args.export_command == 'objects':
                try:
                    logging.info(f"Starting '{args.feature} {args.export_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{fw_name}_{args.type}_{args.export_command}_{args.option}.xlsx'
                    if args.option == 'all':
                        dfs = [
                            api.export_network_objects(args.type),
                            api.export_network_group_objects(args.type),
                            api.export_service_objects(args.type),
                            api.export_service_group_objects(args.type)
                        ]
                        sheet_names = [
                            'network',
                            'network group',
                            'service',
                            'service group'
                        ]
                    elif args.option == "network":
                        dfs = api.export_network_objects(args.type)
                        sheet_names = args.option
                    elif args.option == "network-group":
                        dfs = api.export_network_group_objects(args.type)
                        sheet_names = args.option
                    elif args.option == "service":
                        dfs = api.export_service_objects(args.type)
                        sheet_names = args.option
                    elif args.option == "service-group":
                        dfs = api.export_service_group_objects(args.type)
                        sheet_names = args.option
                    
                    api.save_dfs_to_excel(dfs, sheet_names, file_name)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")
            
            elif args.export_command == 'hitcount':
                try:
                    logging.info(f"Starting '{args.feature} {args.export_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{fw_name}_{args.type}_{args.export_command}.xlsx'
                    df = api.export_hit_count(args.vsys)
                    sheet_names = args.export_command
                    api.save_dfs_to_excel(df, sheet_names, file_name)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")
        
        elif args.feature == 'analyze':
            if args.analyze_command == 'redundant':
                try:
                    logging.info(f"Starting '{args.feature} {args.analyze_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{fw_name}_{args.type}_{args.analyze_command}.xlsx'
                    sheet_names = args.analyze_command
                    rule_df = api.export_security_rules(args.type)
                    analysis_module.analyze_redundant_policies(rule_df, 'paloalto', file_name)
                    logging.info(f"Completed '{args.feature} {args.analyze_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.analyze_command}': {e}")
            
            elif args.analyze_command == 'validation':
                try:
                    logging.info(f"Starting '{args.feature} {args.analyze_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{fw_name}_{args.type}_{args.analyze_command}.xlsx'
                    running_df = api.export_security_rules('running')
                    candidate_df = api.export_security_rules('candidate')
                    analysis_module.compare_and_save_firewall_policies(running_df, candidate_df, file_name)
                    logging.info(f"Completed '{args.feature} {args.analyze_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.analyze_command}': {e}")
            else:
                logging.error("Invalid Arguments")

def mf2_command(args):
    try:
        hostname_list = args.ip.split(',')
        username = args.username
        password = args.password
    except:
        logging.error("Invalid Arguments")
    
    for hostname in hostname_list:
        setup_logging(hostname)
        if args.feature == 'show':
            if args.show_command == 'info':
                try:
                    logging.info(f"Starting '{args.feature} {args.show_command}'")
                    info = secui_mf2.show_system_info(hostname, 22, username, password)
                    print(info)
                    logging.info(f"Completed '{args.feature} {args.show_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.show_command}': {e}")
        elif args.feature == 'export':
            if args.export_command == 'rules':
                try:
                    logging.info(f"Starting '{args.feature} {args.export_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{hostname}_{args.export_command}.xlsx'
                    rule_df = secui_mf2.export_security_rules(hostname, username, password)
                    secui_mf2.save_dfs_to_excel(rule_df, args.export_command, file_name)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")

            elif args.export_command == 'object':
                try:
                    logging.info(f"Starting '{args.feature} {args.export_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{hostname}_{args.export_command}.xlsx'
                    dfs = secui_mf2.export_objects(hostname, username, password)
                    secui_mf2.save_dfs_to_excel(dfs, ['address', 'address_group', 'service'], file_name)
                    logging.info(f"Completed '{args.feature} {args.export_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")
        
        elif args.feature == 'analyze':
            if args.analyze_command == 'redundant':
                try:
                    logging.info(f"Starting '{args.feature} {args.analyze_command}'")
                    current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                    file_name = f'{current_date}_{hostname}_{args.analyze_command}.xlsx'
                    rule_df = secui_mf2.export_security_rules(hostname, username, password)
                    analysis_module.analyze_redundant_policies(rule_df, 'mf2', file_name)
                    logging.info(f"Completed '{args.feature} {args.analyze_command}'")
                except Exception as e:
                    logging.exception(f"Exception in '{args.feature} {args.analyze_command}': {e}")
            else:
                logging.error("This command is currently not supported")
        else:
            logging.error("This command is currently not supported")


def ngf_command(args):
    if ',' in args.ip:
        logging.error("NGF does not support multiple devices")
        return False
    
    hostname = args.ip
    client_id = args.username
    client_secret = args.password
    
    setup_logging(hostname)
    if args.feature == 'export':
        if args.export_command == 'rules':
            try:
                logging.info(f"Starting '{args.feature} {args.export_command}'")
                current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                file_name = f'{current_date}_{hostname}_{args.export_command}.xlsx'
                rule_df = secui_ngf.export_security_rules(hostname, client_id, client_secret)
                secui_ngf.save_dfs_to_excel(rule_df, args.export_command, file_name)
                logging.info(f"Completed '{args.feature} {args.export_command}'")
            except Exception as e:
                logging.exception(f"Exception in '{args.feature} {args.export_command}': {e}")
    
    elif args.feature == 'analyze':
        if args.analyze_command == 'redundant':
            try:
                logging.info(f"Starting '{args.feature} {args.analyze_command}'")
                current_date = time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime())
                file_name = f'{current_date}_{hostname}_{args.analyze_command}.xlsx'
                rule_df = secui_ngf.export_security_rules(hostname, client_id, client_secret)
                analysis_module.analyze_redundant_policies(rule_df, 'ngf', file_name)
                logging.info(f"Completed '{args.feature} {args.analyze_command}'")
            except Exception as e:
                logging.exception(f"Exception in '{args.feature} {args.analyze_command}': {e}")
        else:
            logging.error("This command is currently not supported")
    else:
        logging.error("This command is currently not supported")

def main():
    parser = argparse.ArgumentParser(prog='FPAT', description='FPAT | Firewall Policy Analysis Tool')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 2.1.0')

    subparsers = parser.add_subparsers(dest='feature', required=True)

    def add_common_args(subparser):
        parser.add_argument('model', type=str, choices=['paloalto', 'mf2', 'ngf'], help='Firewall Model')
        parser.add_argument('username', type=str, help='Username(NGF: Client ID)')
        parser.add_argument('password', type=str, help='Password(Client Secret)')
        parser.add_argument('ip', type=str, help='Firewall IP Address e.g. 192.168.0.1,192.168.0.2...')

    # show
    parser_show = subparsers.add_parser('show', help='Show Information')
    subparsers_show = parser_show.add_subparsers(dest='show_command', required=True)
    subparsers_show.add_parser('info', help='Show System Information')
    subparsers_show.add_parser('thresholds', help='Show Thresholds')
    add_common_args(parser_show)

    # export
    parser_export = subparsers.add_parser('export', help='Export Information')
    parser_export.add_argument('--type', type=str, choices=['running', 'candidate'], default='running', help='Configuration Type')
    # export config
    subparsers_export = parser_export.add_subparsers(dest='export_command', required=True)
    subparsers_export.add_parser('config', help='Export Configuration')
    # export rules
    subparsers_export.add_parser('rules', help='Export Security Rules')
    # export objects
    parser_export_objects = subparsers_export.add_parser('objects', help='Export Objects')
    parser_export_objects.add_argument('--option', type=str, choices=['all', 'network', 'network-group', 'service', 'service-group'], default='all', help='Object Type')
    # export hitcount
    parser_export_hitcount = subparsers_export.add_parser('hitcount', help='Export Hit Count')
    parser_export_hitcount.add_argument('--vsys', type=str, default='vsys1', help='Vsys Name')
    add_common_args(parser_export)

    # analyze
    parser_analyze = subparsers.add_parser('analyze', help='Analyze Information')
    parser_analyze.add_argument('--type', type=str, choices=['running', 'candidate'], default='running', help='Configuration Type')
    subparsers_analyze = parser_analyze.add_subparsers(dest='analyze_command', required=True)
    # analyze redundant
    subparsers_analyze.add_parser('redundant', help='Analyze Redundant Policies')
    # analyze validation
    subparsers_analyze.add_parser('validation', help='Analyze Validation')
    add_common_args(parser_analyze)

    args = parser.parse_args()

    if args.feature == 'deletion':
        deletion_process.deletion_process_main()
    else:
        try:
            if args.model == 'paloalto':
                paloalto_command(args)
            elif args.model == 'mf2':
                mf2_command(args)
            elif args.model == 'ngf':
                ngf_command(args)
        except ValueError as e:
            logging.exception(f"Exception: {e}")
            return

if __name__ == '__main__':
    main()