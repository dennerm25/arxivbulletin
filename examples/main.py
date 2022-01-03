import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.split(os.getcwd())[0],'src/'))
from arxivbulletin import arxivbulletin


arxivsummary = arxivbulletin()
arxivsummary.send_report()
#arxivsummary.save()
