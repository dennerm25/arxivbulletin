# ArXiv Bulletin
This python tool allows to filter ArXiv papers based on keywords and author names, and report them via terminal or email. Thank you to arXiv for use of its open access interoperability.

## Setup

 - **config.py**: Personalization file, containing four possible entries:
	- *name*: Your name, to personalize ArXiv Bulletin messages
    - *email*: Your email address, to send ArXiv Bulletin messages by mail. If "None", the messages will be printed to the terminal
    - *password*: Your email password, to send emails without user input. If "None", a user prompt will require a password entry.
    - *categories*: A list of the ArXiv categories that should be checked ([For a list of all categories take a look here](https://arxiv.org/category_taxonomy))

 - **keywords.txt** (optional): A row-wise collection of keywords, used to filter ArXiv papers. If not provided and no author names (see below) are available, results are not filtered.
 - **keyauthors.txt** (optional): A row-wise collection of author names, used to filter ArXiv papers. If not provided and no keywords (see above) are available, results are not filtered.

### Receiving ArXiv messages per mail
ArXiv Bulletin can send personalized messages to your mail account, currently restricted to Google Mail. A new account can be created [here](https://accounts.google.com/signup). In your account settings, make sure to set *Allow less secure apps* to *on*. Note that currently there is no workaround for storing the email password in plain text or requiring user input.

## Usage

Import the arxivbulletin class
```
from arxivbulletin import arxivbulletin
```
Create arxivbulletin object
```
arxivsummary = arxivbulletin(start_date, end_date)
```
where `start_date` and `end_date` are optional `datetime` objects specifying the timespan to be checked for relevant papers. If `start_date` and `end_date` are not provided, ArXivBulletin uses the current date.

Get summary based on (optional) keywords and keyauthors

```
arxivsummary.send_report()
```
To save reports, call
```
arxivsummary.save(filenamerec="arxivrecords.csv", filenamefil="arxivfilters.csv")
```
where `filenamerec` and `filenamefil` are optional parameters for storing all ArXiv papers and their label (0 - not included in filtered list / 1 - included in report), respectively. 

### Example usage

In order to obtain a daily selection of ArXiv submissions based on your preferences, create a file `main.py`, containing
```
from arxivbulletin import arxivbulletin
arxivsummary = arxivbulletin()
arxivsummary.send_report()
```
and run from the terminal once a day.

## Automation
In order to automate the execution of, for instance, `main.py` above, MacOS users can rely on `cron`. Running `crontab -e` in a terminal opens a cron file where a job can be added by `esc` + `i`. Adding the following line

```
* * * * * /PathToPython /path/to/file/arXivbulletin/main.py
```
runs the file `main.py` every minute. The timing can be adjusted by replacing the appropriate `*`, whereby the

1. `*` describes the minute,
2. `*` the hour,
3. `*` the day of the month,
4. `*` the month,
5. `*` the day of the week.

Save and quit the file by `esc` + `wq`. All cron jobs can be viewed by `crontab -l`.

Note that the execution might require terminal and cron to have full disk access, which can be found in `Settings`-`Security & Privacy`- `Full Disk Access`. To include `cron`, hit `+` followed by `Command + Shift + G` and move to `/usr/sbin/cron`, then restart your device.

More information (including troubleshooting and an untested option for windows users) can for instance be found [here](https://towardsdatascience.com/how-to-easily-automate-your-python-scripts-on-mac-and-windows-459388c9cc94).

**Note that this will only work if your machine is awake, neither in stand-by nor turned off.** 

## License

This project is licensed under the MIT License - see the LICENSE file for details.

