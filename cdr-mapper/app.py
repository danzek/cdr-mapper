#!/usr/bin/env python
"""
CDR Mapper GUI application
"""

import easygui
import os
import sys
from models import Database, TollsCase, Tower, CDR, Report


__author__ = "Dan O'Day"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Dan O'Day"
__email__ = "d@4n68r.com"
__status__ = "Prototype"


RESOURCES_FOLDER = '/Users/danoday/Dropbox/dev/cdr-mapper/cdr-mapper/cdr-mapper/resources'


def validate_fields(fields):
    for field in fields:
        if field.strip() == '' or not field.strip():
            return False
    return True

def get_case_details():
    form_fields = ['Case Number', 'Agency', 'Agent', 'Analyst', 'Target Number']
    case_details = []
    case_details = easygui.multenterbox("Complete the basic case information.", title="Case Information",
                                        fields=form_fields, values=case_details)
    valid = validate_fields(case_details)
    while not valid:
        easygui.msgbox("Missing required case fields.", title="Error")
        case_details = get_case_details()
        valid = validate_fields(case_details)

    return dict(zip(form_fields, case_details))


def get_file(message):
    return easygui.fileopenbox(msg=message, title="Select File", filetypes=["*.txt", "*.csv"])


def parse_same_file():
    pass


def parse_two_files():
    case_details = get_case_details()
    tower_data = get_file("Please select the CSV file containing the tower data.")


def main():
    easygui.buttonbox('''CDR Mapper is provided under the terms of the MIT License: THIS SOFTWARE IS PROVIDED "AS
    IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
    MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
    COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.'''.replace('\n', ''),
                   title="DISCLAIMER", choices=["I accept these terms"],
                   image=os.path.join(RESOURCES_FOLDER, 'tower.gif'))

    if easygui.ynbox(msg="Are your CDR and cell site / tower data in the same file?", title="Main Menu"):
        parse_same_file()
    else:
        parse_two_files()


def initialize_database():
    """
    Initializes database.
    :return: prints status of database to console
    """
    database = Database()
    if not os.path.isfile(database.database_filename):
        database.create_tables()
        print 'Database tables created successfully. Filename:', database.database_filename
    else:
        print 'Database already initialized. Filename:', database.database_filename


if __name__ == '__main__':
    initialize_database()
    main()
    sys.exit(0)