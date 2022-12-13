# check-mullvad-account-exp

[![CI](https://github.com/stefankonig/check-mullvad-account-exp/actions/workflows/lint-test.yml/badge.svg)](https://github.com/stefankonig/check-mullvad-account-exp/actions/workflows/lint-test.yml)

Icinga check to monitor whether your Mullvad VPN account needs a top-up.  
The script has been written and tested on python 3.8, 3.9 & 3.10 for usage on Ubuntu 20.04/22.04 or Debian 11.

```console
foo@bar:~$ ./check_mullvad_account_exp.py --help
usage: check_mullvad_account_exp.py [-h] --account <YOUR_ACCOUNT_NUMBER> [--warning <DAYS>] [--critical <DAYS>] [--verbose]

Mullvad account expiration date checker

optional arguments:
  -h, --help            show this help message and exit
  --warning <DAYS>, -w <DAYS>
                        warning days
  --critical <DAYS>, -c <DAYS>
                        critical days
  --verbose, -v

required arguments:
  --account <YOUR_ACCOUNT_NUMBER>, -a <YOUR_ACCOUNT_NUMBER>
                        Mullvad account-number to check (int)
```

The check fetches your account data from `https://api.mullvad.net/www/accounts/<account>` and parses the expiry date.  
I figure you only need to run this once a day, keeping our fellows at Mullvad happy as well.


## Icinga CheckCommand definition
```
object CheckCommand "mullvad-account-exp" {
    import "plugin-check-command"
    command = [ PluginDir + "/check_mullvad_account_exp.py" ]
    timeout = 2m
    arguments += {
        "-a" = {
            description = "Account number"
            required = true
            value = "$mullvad_account$"
        }
        "-c" = {
            description = "Critical days"
            required = false
            value = "$mullvad_critical$"
        }
        "-w" = {
            description = "Warning days"
            required = false
            value = "$mullvad_warning$"
        }
    }
}
```

Additionally, add `mullvad_account` to the *Protected Custom Variables* in the monitoring module of icingaweb2 so it wont show up in plaintext. 

GLHF.