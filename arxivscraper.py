#####

# Inspired by:
# https://github.com/mahdisadjadi/arxivscraper
# https://github.com/blairbilodeau/arxiv-biorxiv-search

######################################################################

# Packages
import datetime
import os
import xml.etree.ElementTree as ET
import gc
import pandas as pd
import urllib, urllib.request
import smtplib, ssl
import sys
import numpy as np
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Config file
import config as cfg

# Custom exception if no submissions were found
class SubmissionError(Exception):
    pass

# Arxiv Scraper class
class arxivscraper:

    def __init__(self, start=datetime.date.today(), end=datetime.date.today()):
        # Begin of timespan
        self.start = start
        # End of timespan
        self.end = end
        # Path to current directory
        self.path = os.getcwd()
        # Open and read (if possible) user provided search keywords
        self.keywords = self.openfile('keywords.txt')
        self.keyauthors = self.openfile('keyauthors.txt')
        # Open and read (if possible) user provided data
        self.name = cfg.myconfig["name"]
        self.email = cfg.myconfig["email"]
        self.password = cfg.myconfig["password"]
        self.categories = cfg.myconfig["categories"]
        # Get submissions for selected timespan and categories
        self.get_submissions()

        # If keywords and keyauthors are not provided by the user, collect all submissions
        if len(self.keywords) == 0 and len(self.keyauthors) == 0:
            self.records_df_filtered = self.records_df
            self.num_records_filtered = len(self.records_df_filtered)
            print("Submissions were not filtered, provide keywords or authors")
        else:
            # Filter by keywords and keyauthors
            self.filter()


    def openfile(self, fn):
        # open and read from user provided files
        try:
            results = []
            with open(os.path.join(self.path, fn)) as f:
                for line in f:
                    results.append(line.strip())
            return results
        # if files do not exist, create empty array
        except IOError:
            results = []
            return results

    def extract_data(self, metadata, key):
        # extract human readable text from metadata
        ARXIV = '{http://arxiv.org/OAI/arXiv/}'
        return [meta.find(ARXIV + key).text.strip().lower().replace('\n', ' ') for meta in metadata]

    def extract_authorlist(self, author_lists):
        ARXIV = '{http://arxiv.org/OAI/arXiv/}'

        ## extract first and last names, clean them, and put them together to make human readable
        last_name_lists = [[author.find(ARXIV + 'keyname').text.lower() for author in author_list] for author_list in author_lists]
        first_name_meta_lists = [[author.find(ARXIV + 'forenames') for author in author_list] for author_list in author_lists]
        first_name_lists = [['' if name == None else name.text.lower() for name in first_name_meta_list] for first_name_meta_list in first_name_meta_lists]
        full_name_temp_lists = [zip(a,b) for a,b in zip(first_name_lists, last_name_lists)]
        full_name_lists = [[a+' '+b for a,b in full_name_temp_list] for full_name_temp_list in full_name_temp_lists]
        return full_name_lists

    def get_submissions(self):

        OAI = '{http://www.openarchives.org/OAI/2.0/}'
        ARXIV = '{http://arxiv.org/OAI/arXiv/}'

        records_df = pd.DataFrame(columns=['title','abstract', 'abstract_title_concats', 'url','authors', 'date'])

        for cat in self.categories:
            # Fetch from arXiv API for each category
            url = 'http://export.arxiv.org/oai2?verb=ListRecords&from=' + str(self.start) + '&until=' + str(self.end) + '&metadataPrefix=arXiv&set=' + cat
            data = urllib.request.urlopen(url)
            xml = data.read() # get raw xml data from server
            gc.collect()
            xml_root = ET.fromstring(xml)
            records = xml_root.findall(OAI + 'ListRecords/' + OAI + 'record') # list of all records from xml tree

            ## extract metadata for each record
            metadata = [record.find(OAI + 'metadata').find(ARXIV + 'arXiv') for record in records]

            ## use metadata to get info for each record
            titles = self.extract_data(metadata, 'title')
            abstracts = self.extract_data(metadata, 'abstract')
            created = self.extract_data(metadata, 'created')
            urls = ['https://arxiv.org/abs/' + link for link in self.extract_data(metadata, 'id')]
            author_lists = [meta.findall(ARXIV + 'authors/' + ARXIV + 'author') for meta in metadata]
            abstract_title_concats = [title+'. '+abstract for title,abstract in zip(titles,abstracts)]
            full_name_lists = self.extract_authorlist(author_lists)

            ## compile all info into big dataframe
            records_data = list(zip(titles, abstracts, abstract_title_concats, urls, full_name_lists, created))
            records_df_tmp = pd.DataFrame(records_data,columns=['title','abstract', 'abstract_title_concats', 'url','authors', 'date'])

            # Append to existing dataframe
            records_df = records_df.append(records_df_tmp, ignore_index=True)

        self.records_df = records_df
        self.num_records = len(self.records_df)



    def filter(self):
        # So far brute force, include up to a week in advance for submissions created earlier, yet exclude replacements, doesn't work for beginning of months
        #datelist = [str(self.end.replace(day=self.end.day-i)) for i in range(8)]

        # Check for entries matching keywords, authors and dates
        kwd_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([kwd in x for kwd in self.keywords]), self.records_df.abstract_title_concats))) if val])
        auth_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([auth in x for auth in self.keyauthors]), self.records_df.authors))) if val])
        #date_idxs = set([idx for idx,val in enumerate(list(map(lambda x: any([date in x for date in datelist]), self.records_df.date))) if val])

        # Combine criteria
        idxs = set.union(kwd_idxs,auth_idxs)
        #idxs = set.intersection(idxs,date_idxs)
        label = np.zeros(self.num_records)
        label[list(idxs)] = 1

        # Filter data
        self.records_df_filtered = self.records_df.iloc[list(idxs)]
        self.num_records_filtered = len(self.records_df_filtered)
        self.filter_idxs = label

#    def create_report(self):
#        if self.num_records == 0:
#            raise SubmissionError()
#
#
#        if self.end != self.start:
#            timespan = "from " + str(self.start) + " to " + str(self.end)
#        else:
#            timespan = "for " + str(self.end)
#        # Compile message
#        message = f"""Subject: ArXiv summary {timespan}
#
#Dear {self.name},
#today there were {self.num_records} preprints on arXiv, out of which {self.num_records_filtered} were relevant for you.
#_____________________________________________________________________________"""+ "\n"
#
#        for i in range(self.num_records_filtered):
#
#            header = " ".join(self.records_df_filtered.iloc[i].title.split()) + "\n" + "\n"
#            body = self.records_df_filtered.iloc[i].abstract+ "\n"
#            link = self.records_df_filtered.iloc[i].url + "\n"
#            delimiter = """_____________________________________________________________________________"""+ "\n"
#            message+=header+body+link+delimiter
#
#        return message

    def create_report(self):
        # If there are no submissions, raise error and stop
        if self.num_records == 0:
            raise SubmissionError()

        # Get time span or date
        if self.end != self.start:
            timespan = "from " + str(self.start) + " to " + str(self.end)
        else:
            timespan = "for " + str(self.end)

        # Set up email message
        message = MIMEMultipart("alternative")
        message["Subject"] = f"ArXiv summary {timespan}"
        message["From"] = self.email
        message["To"] = self.email

        # Create the plain-text and HTML version of the message
        text = f"""Dear {self.name},
        Today there were {self.num_records} preprints on arXiv, out of which {self.num_records_filtered} were relevant for you.
        _____________________________________________________________________________"""+ "\n"

        # Add papers
        for i in range(self.num_records_filtered):
            header = " ".join(self.records_df_filtered.iloc[i].title.title().split()) + "\n" + "\n"
            body = self.records_df_filtered.iloc[i].abstract+ "\n"
            link = self.records_df_filtered.iloc[i].url + "\n"
            delimiter = """_____________________________________________________________________________"""+ "\n"
            text+=header+body+link+delimiter

        html = "<html><body><p>Dear " + self.name +",<br>Today there were "+str(self.num_records)+" preprints on arXiv, out of which "+str(self.num_records_filtered)+" were relevant for you.<br><hr></p>"""
        # Add papers
        for i in range(self.num_records_filtered):
            header = "<p><a href=" + self.records_df_filtered.iloc[i].url + ">" + " ".join(self.records_df_filtered.iloc[i].title.title().split()) + "</a><br><br>"
            body = self.records_df_filtered.iloc[i].abstract+ "<br><hr></p>"
            html+=header+body
        html += "</body></html>"

        # Turn these into plain/html MIMEText objects
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        # Add HTML/plain-text parts to MIMEMultipart message
        # The email client will try to render the last part first
        message.attach(part1)
        message.attach(part2)

        return message


    def send_report(self):
        # if no email address stored, print to terminal
        if self.email is None:
            try:
                message = self.create_report()
                print(message.get_payload()[0])

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

        # if no password stored, ask user for access
        elif self.password is None:
            try:
                message = self.create_report()

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

            pwrd = input("Type your e-mail password and press enter: ")
            port = 465  # For SSL
            # Create a secure SSL context
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                # Login
                server.login(self.email, pwrd)
                # Send message
                server.sendmail(self.email, self.email, message.as_string())

        # if email and password given, send message
        else:
            try:
                message = self.create_report()

            except SubmissionError:
                sys.stderr.write('No ArXiv submissions for selected timespan! \n')
                exit(-1)

            port = 465  # For SSL
            # Create a secure SSL context
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
                # Login
                server.login(self.email, self.password)
                # Send message
                server.sendmail(self.email, self.email, message.as_string())

    def save(self, filenamerec="arxivrecords.csv", filenamefil="arxivfilters.csv"):
        # Store collected arxiv papers
        with open(filenamerec, 'a') as f:
            self.records_df.to_csv(f, header=f.tell()==0)
        # Store indexes of selected entries
        with open(filenamefil, 'a') as f:
            np.savetxt(f, self.filter_idxs, '%s', ',')
