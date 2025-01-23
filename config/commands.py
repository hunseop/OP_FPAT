COMMANDS = {
    "paloalto": {
        "show": {
            "info": None,
            "thresholds": None,
        },
        "export": {
            "config": {
                "options": {
                    "type": ["running", "candidate"]
                }
            },
            "rules": {
                "options": {
                    "type": ["running", "candidate"]
                }
            },
            "objects": {
                "options": {
                    "type": ["running", "candidate"],
                    "option": ["all", "network", "network-group", "service", "service-group"]
                }
            },
            "hitcount": {
                "options": {
                    "vsys": "vsys1"
                }
            }
        },
        "analyze": {
            "redundant": {
                "options": {
                    "type": ["running", "candidate"]
                }
            },
            "validation": None
        }
    },
    "mf2": {
        "show": {
            "info": None
        },
        "export": {
            "rules": None,
            "objects": None
        },
        "analyze": {
            "redundant": None
        }
    },
    "ngf": {
        "export": {
            "rules": None,
        },
        "analyze": {
            "redundant": None
        }
    }
}

SUBCOMMAND_FUNCTIONS = {
    "paloalto": {
        "show": {
            "info": paloalto_show_info,
            "thresholds": paloalto_show_thresholds
        },
        "export": {
            "config": paloalto_export_config,
            "rules": paloalto_export_rules,
            "objects": paloalto_export_objects,
            "hitcount": paloalto_export_hitcount,
        },
        "analyze": {
            "redundant": paloalto_analyze_redundant,
            "validation": paloalto_analyze_compare_policies
        }
    }
}