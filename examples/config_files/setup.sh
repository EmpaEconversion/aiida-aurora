
verdi computer setup --config computer_ddm07162.yml
verdi computer configure ssh2win --config computer_ddm07162_config.yaml ddm07162

verdi computer setup --config computer_localhost.yml
verdi computer configure core.local --config computer_localhost_config.yaml localhost

verdi computer setup --config computer_localhost-verdi.yml
verdi computer configure core.local --config computer_localhost-verdi_config.yaml localhost-verdi

verdi code setup --config code_ketchup-0.2rc2.yml
verdi code setup --config code_monitor.yml
