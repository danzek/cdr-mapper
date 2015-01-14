#!/usr/bin/env python
"""
CDR Mapper GUI application
"""

import csv
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


RESOURCES_FOLDER = r'C:\Users\dday\PycharmProjects\cdr-mapper\cdr-mapper\resources'


def validate_fields(fields):
    """
    Check if all fields in list have values
    :param fields: list containing values to check
    :return: True if all fields have values, False otherwise
    """
    for field in fields:
        if field.strip() == '' or not field:
            return False
    return True


def get_case_details():
    """
    Get case information
    :return: primary key of TollsCase entry
    """
    form_fields = ['Case Number', 'Agency', 'Agent', 'Analyst', 'Target Number']
    case_details = []
    valid = False
    i = 1

    while not valid:
        if i > 1:
            if i > 2:  # prevent user from being stuck in loop if trying to cancel and quit
                if easygui.ynbox("Do you wish to exit the program?", title="Exit?"):
                    sys.exit(0)
            case_details = []
            easygui.msgbox("Missing required case fields.", title="Error")

        case_details = easygui.multenterbox("Complete the basic case information.", title="Case Information",
                                            fields=form_fields, values=case_details)
        if case_details:
            valid = validate_fields(case_details)
        i += 1

    tc = TollsCase(case_details[0], case_details[1], case_details[2], case_details[3], case_details[4])
    tc.save()
    return tc.case_unique_id


def get_csv_headers(path):
    """
    Extract headers from CSV file
    :param path: file path to CSV file
    :return: list containing headers in original order
    """
    headers = []
    i = 0
    while not headers:
        try:
            i += 1
            with open(path, 'rb') as f:
                f_csv = csv.reader(f)
                headers = next(f_csv)
        except IOError:
            easygui.msgbox(msg="There was an error accessing this file.")
            path = get_file("Please try selecting the CSV file again.")
            if i > 1:
                easygui.exceptionbox()
                sys.exit(0)
    return headers


def get_file(message):
    """
    Get file
    :param message: msg displayed to user in dialog window
    :return: file path
    """
    f = None
    while not f:
        f = easygui.fileopenbox(msg=message, title="Select File", filetypes=["*.txt", "*.csv"])
    return f


def get_save_location(message):
    """
    Get location to save file
    :param message: msg displayed to user in dialog window
    :return: directory path
    """
    d = None
    while not d:
        d = easygui.diropenbox(msg=message, title="Select Save Location")
    return d


def import_tower_data(case_id):
    """
    Imports tower data when towers are separate from CDR data
    :param case_id: primary key of case
    :return: n/a
    """
    cell_site = None
    latitude = None
    longitude = None
    sector = None
    azimuth = None

    easygui.msgbox(msg=' '.join(["Your cell site / tower data must be in CSV format and have the following REQUIRED",
                                "fields: Cell Site ID, Latitude, Longitude, Sector, and Azimuth."]), title="Towers")

    tower_file = get_file("Please select the CSV file containing the tower data.")
    headers = get_csv_headers(tower_file)

    # get required tower fields
    while not latitude:
        latitude = easygui.choicebox("Select the column heading that corresponds to the latitude.",
                                     title="Get Latitude", choices=headers)

    while not longitude:
        longitude = easygui.choicebox("Select the column heading that corresponds to the longitude.",
                                      title="Get Longitude", choices=headers)

    while not cell_site:
        cell_site = easygui.choicebox("Select the column heading that corresponds to the cell site / tower ID.",
                                      title='Get Cell Site ID', choices=headers)

    while not sector:
        sector = easygui.choicebox("Select the column heading that corresponds to the sector.",
                                   title="Get Sector", choices=headers)

    while not azimuth:
        azimuth = easygui.choicebox("Select the column heading that corresponds to the azimuth.",
                                    title="Get Azimuth", choices=headers)

    # populate variables with index for each header column
    i_cell_site = headers.index(cell_site)
    i_latitude = headers.index(latitude)
    i_longitude = headers.index(longitude)
    i_sector = headers.index(sector)
    i_azimuth = headers.index(azimuth)

    easygui.msgbox(msg=' '.join(["Importing the towers may take several minutes. The application will run in the",
                                 "background while the tower import process is running. A message will be displayed",
                                 "to you once the import is finished. Click OK to begin the import."]),
                   title="Loading Warning")

    with open(tower_file, 'rb') as f:
        f_csv = csv.reader(f)
        discarded_headers = next(f_csv)

        for row in f_csv:
            t = Tower(case_id, row[i_cell_site], row[i_latitude], row[i_longitude], row[i_sector], row[i_azimuth])
            t.save()

    easygui.msgbox(msg='Towers imported successfully.', title="Success")


def import_cdrs(case_id):
    """
    Imports CDR data when CDRs are separate from tower data
    :param case_id: primary key of case
    :return: n/a
    """
    called_number = None
    cell_site_id = None
    sector = None
    other_fields = None

    easygui.msgbox(msg=' '.join(["Your CDR data must be in CSV format and have the following REQUIRED fields:",
                                 "Cell Site ID, Called Number, and Sector."]), title="CDRs")

    cdr_file = get_file("Please select the CSV file containing the CDR data.")
    headers = get_csv_headers(cdr_file)

    # get required CDR fields
    while not called_number:
        called_number = easygui.choicebox(' '.join(["Select the column heading that corresponds to the called (or",
                                                    "non-target) number."]), title="Get Number", choices=headers)

    while not cell_site_id:
        cell_site_id = easygui.choicebox("Select the column heading that corresponds to the cell site / tower ID.",
                                         title='Get Cell Site ID', choices=headers)

    while not sector:
        sector = easygui.choicebox("Select the column heading that corresponds to the sector.",
                                   title="Get Sector", choices=headers)

    while not other_fields:
        other_fields = easygui.multchoicebox(' '.join(["Select all of the columns you wish to appear in the",
                                                       "description for each point on the map."]),
                                             title="Get Report Fields", choices=headers)

    # populate variables with index for each header column
    i_called_number = headers.index(called_number)
    i_cell_site_id = headers.index(cell_site_id)
    i_sector = headers.index(sector)
    knowns = [i_called_number, i_cell_site_id, i_sector]
    d_other_fields = {of: headers.index(of) for of in other_fields if headers.index(of) not in knowns
                      and of.strip() != ''}  # remove knowns

    easygui.msgbox(msg=' '.join(["Importing the CDRs may take several minutes. The application will run in the",
                                 "background while the CDR import process is running. A message will be displayed",
                                 "to you once the import is finished. Click OK to begin the import."]),
                   title="Loading Warning")

    with open(cdr_file, 'rb') as f:
        f_csv = csv.reader(f)
        discarded_headers = next(f_csv)

        for row in f_csv:
            report_fields = {}
            for k, v in d_other_fields.iteritems():
                report_fields[k] = row[v]

            cdr = CDR(case_id, row[i_called_number], row[i_cell_site_id], row[i_sector], report_fields)
            cdr.save()

    easygui.msgbox(msg='CDRs imported successfully.', title="Success")


def parse_same_file(case_id):
    """
    Handles report when CDRs and cell sites / towers are in same file
    :param case_id: primary key of case
    :return: n/a
    """
    data = get_file("Please select the CSV file containing the CDR and tower data.")
    headers = get_csv_headers(data)
    # TODO -- select headers from imported data


def parse_two_files(case_id):
    """
    Handles report when CDRs and cell sites / towers are in separate files
    :param case_id: primary key of case
    :return: n/a
    """
    import_tower_data(case_id)
    import_cdrs(case_id)
    save_location = get_save_location("Please select the folder where you want to save the report.")
    final_report = Report(case_id, save_location)

    report_name = None
    i = 0
    while not report_name:
        try:
            i += 1
            report_name = final_report.generate_map()
        except IOError:
            easygui.msgbox(msg="There was an error writing the report file.")
            report_name = get_file("Please select the location where you wish to save the report again.")
            if i > 1:
                easygui.exceptionbox()
                sys.exit(0)

    easygui.msgbox(msg=' '.join(["Report successfully saved to", report_name]), title="Success")


def main():
    """
    Main routine: shows disclaimer, initializes database, gets case details, determines which files to parse
    :return: n/a
    """
    easygui.buttonbox(msg=' '.join(['CDR Mapper\n', '--------------------------\n',
                                    'CDR Mapper will plot CDR and cell site / tower data in a map file that can be',
                                    'opened using Google Earth.\n\n'
                                    'CDR Mapper is provided under the terms of the MIT License:\n\nTHIS SOFTWARE IS',
                                    'PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT',
                                    'NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR',
                                    'PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS',
                                    'BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF',
                                    'CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE',
                                    'SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE. USE OF THIS SOFTWARE',
                                    'CONSTITUTES ACCEPTANCE OF THESE TERMS.\n\nCopyright (c) 2015 Dan O\'Day']),
                      title="DISCLAIMER", choices=["I understand and accept these terms"],
                      image=os.path.join(RESOURCES_FOLDER, 'tower.gif'))

    initialize_database()
    case_id = get_case_details()

    if easygui.ynbox(msg="Are your CDR and cell site / tower data in the same CSV file?", title="Main Menu"):
        parse_same_file(case_id)
    else:
        parse_two_files(case_id)


def initialize_database():
    """
    Initializes database
    :return: destroys existing database and creates new one for new case
    """
    database = Database()
    if not os.path.isfile(database.database_filename):
        database.create_tables()
    else:
        destroy_database()
        database.create_tables()


def destroy_database():
    """
    Delete sqlite database
    :return: database is deleted
    """
    database = Database()
    if os.path.isfile(database.database_filename):
        os.remove(database.database_filename)


if __name__ == '__main__':
    main()
    sys.exit(0)