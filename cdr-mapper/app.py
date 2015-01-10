#!/usr/bin/env python
"""
CDRMapper Flask app.
"""

import csv
import flask
import os
import time
from werkzeug.utils import secure_filename
from models import Database, TollsCase, Tower, CDR, Report

__author__ = "Dan O'Day"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Dan O'Day"
__email__ = "d@4n68r.com"
__status__ = "Prototype"


UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = set(['txt', 'csv'])

app = flask.Flask(__name__)


def allowed_file(filename):
    """
    Checks if file name is allowed based on ALLOWED_EXTENSIONS
    :param filename: file name being checked
    :return: boolean -- true or false
    """
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return flask.render_template('index.html')

@app.route('/case-form/', methods=['GET', 'POST'])
def case_form():
    if flask.request.method == 'POST':
        case_number = flask.request.form['casenum']
        agency = flask.request.form['agency']
        agent = flask.request.form['agent']
        analyst = flask.request.form['analyst']
        target_number = flask.request.form['targetnum']

        if not case_number or not agency or not agent or not analyst or not target_number:
            return flask.render_template('caseform.html', message='Missing required field(s).')

        tc = TollsCase(case_number, agency, agent, analyst, target_number)
        tc.save()
        return flask.redirect(flask.url_for('upload_towers', case_id=tc.case_unique_id))
    else:
        return flask.render_template('caseform.html')

@app.route('/upload/towers/<case_id>', methods=['GET', 'POST'])
def upload_towers(case_id=None):
    if case_id:
        if flask.request.method == 'POST':
            f = flask.request.files['towers']
            if f and allowed_file(f.filename):
                fn = secure_filename(''.join([str(time.time()).replace('.', ''), f.filename]))
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                return flask.redirect(flask.url_for('import_towers', case_id=case_id, filename=fn))
            else:
                return flask.render_template('towerupload.html', cid=case_id,
                                             message='Invalid file format or name. Be sure file is a CSV file and '
                                                     'remove any spaces or special characters in the file name.')
        else:
            return flask.render_template('towerupload.html', cid=case_id)
    else:
        return flask.redirect(flask.url_for('case_form'))


@app.route('/import/towers/<case_id>/<filename>', methods=['GET', 'POST'])
def import_towers(case_id=None, filename=None):
    if case_id:
        if filename:
            case_number = TollsCase.get_case_number(case_id)
            with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
                csv_f = csv.reader(f)
                headers = next(csv_f)

                header_options = ['<option value="{i:d}">{header}</option>'.format(i=headers.index(h), header=h)
                                  for h in headers if h.strip() != '']  # ignore columns with blank headers

                if flask.request.method == 'POST':
                    cell_site_id = int(flask.request.form['cellsite'])
                    latitude = int(flask.request.form['latitude'])
                    longitude = int(flask.request.form['longitude'])
                    sector = int(flask.request.form['sector'])
                    azimuth = int(flask.request.form['azimuth'])

                    if cell_site_id < 0 or latitude < 0 or longitude < 0 or sector < 0 or azimuth < 0:
                        return flask.render_template('towercolumns.html',
                                                     cid=case_id,
                                                     fn=filename,
                                                     casenum=case_number,
                                                     header_list=header_options,
                                                     message='You must select the appropriate column for each '
                                                             'recognized field.')

                    for row in csv_f:
                        t = Tower(case_id, row[cell_site_id], row[latitude], row[longitude], row[sector], row[azimuth])
                        t.save()

                    return flask.redirect(flask.url_for('upload_cdrs', case_id=case_id, filename=filename))
                else:
                    return flask.render_template('towercolumns.html',
                                                 cid=case_id,
                                                 fn=filename,
                                                 casenum=case_number,
                                                 header_list=header_options)
        else:
            return flask.redirect(flask.url_for('upload_towers', case_id=case_id))
    else:
        return flask.redirect(flask.url_for('case_form'))


@app.route('/upload/cdrs/<case_id>/<filename>', methods=['GET', 'POST'])
def upload_cdrs(case_id=None, filename=None):
    if case_id and filename:
        if flask.request.method == 'POST':
            f = flask.request.files['cdrs']
            if f and allowed_file(f.filename):
                fn = secure_filename(''.join([str(time.time()).replace('.', ''), f.filename]))
                f.save(os.path.join(app.config['UPLOAD_FOLDER'], fn))
                return flask.redirect(flask.url_for('import_cdrs', case_id=case_id, filename=fn))
            else:
                return flask.render_template('cdrupload.html', cid=case_id, fn=filename,
                                             message='Invalid file format or name. Be sure file is a CSV file and '
                                                     'remove any spaces or special characters in the file name.')
        else:
            # cleanup - remove uploaded towers file
            if filename != 'deletedtowers89fhYn98f6b2H590562Anf52':  # change filename to this once deleted
                if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    filename = 'deletedtowers89fhYn98f6b2H590562Anf52'  # hopefully unique enough

            return flask.render_template('cdrupload.html',
                                         cid=case_id,
                                         fn=filename)
    else:
        return flask.redirect(flask.url_for('case_form'))


@app.route('/import/cdrs/<case_id>/<filename>', methods=['GET', 'POST'])
def import_cdrs(case_id=None, filename=None):
    if case_id and filename:
        case_number = TollsCase.get_case_number(case_id)
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), 'rb') as f:
            csv_f = csv.reader(f)
            headers = next(csv_f)

            header_options = ['<option value="{i:d}">{header}</option>'.format(i=headers.index(h), header=h)
                              for h in headers if h.strip() != '']  # ignore columns with blank headers

            if flask.request.method == 'POST':
                calling_number = int(flask.request.form['callingnumber'])
                called_number = int(flask.request.form['callednumber'])
                dialed_digits = int(flask.request.form['dialed'])
                call_direction = int(flask.request.form['direction'])
                start_date = int(flask.request.form['start'])
                end_date = int(flask.request.form['end'])
                duration = int(flask.request.form['duration'])
                cell_site_id = int(flask.request.form['cellsite'])
                sector = int(flask.request.form['sector'])

                if called_number < 0 or cell_site_id < 0 or sector < 0:
                    return flask.render_template('cdrcolumns.html',
                                                 cid=case_id,
                                                 fn=filename,
                                                 casenum=case_number,
                                                 header_list=header_options,
                                                 message='Missing required fields.')

                for row in csv_f:
                    cdr = CDR(case_id, return_null_value(row, calling_number), row[called_number],
                              return_null_value(row, dialed_digits), return_null_value(row, call_direction),
                              return_null_value(row, start_date), return_null_value(row, end_date),
                              return_null_value(row, duration), row[cell_site_id], row[sector])
                    cdr.save()

                return flask.redirect(flask.url_for('results', case_id=case_id, filename=filename))
            else:
                return flask.render_template('cdrcolumns.html',
                                             cid=case_id,
                                             fn=filename,
                                             casenum=case_number,
                                             header_list=header_options)
    else:
        return flask.redirect(flask.url_for('case_form'))


@app.route('/results/<case_id>/<filename>')
def results(case_id=None, filename=None):
    if case_id and filename:
        # cleanup - remove uploaded towers file
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        case_details = TollsCase.get_case_details(case_id)
        final_report = Report(case_id, app.config['UPLOAD_FOLDER'])
        report_name = final_report.generate_map()

        return flask.render_template('results.html',
                                     casenum=case_details['Case Number'],
                                     agency=case_details['Agency'],
                                     agent=case_details['Agent'],
                                     analyst=case_details['Analyst'],
                                     targetnum=case_details['Target Number'],
                                     reportfn=report_name)
    else:
        return flask.redirect(flask.url_for('case_form'))

@app.route('/results/<reportname>')
def serve_report(reportname=None):
    return flask.send_from_directory(app.config['UPLOAD_FOLDER'], reportname)


def return_null_value(row, column_index):
    """
    Use blank strings for empty data fields
    :param row: row of data
    :param column_index: index of column being checked in row
    :return: if field in row with given valid index has data, return it; otherwise return empty string.
    """
    return '' if column_index < 0 else row[column_index]


def initialize_database():
    """
    Initializes database.
    :return: prints status of database to screen
    """
    database = Database()
    if not os.path.isfile(database.database_filename):
        database.create_tables()
        print 'Database tables created successfully. Filename:', database.database_filename
    else:
        print 'Database already initialized. Filename:', database.database_filename


if __name__ == '__main__':
    app.debug = True
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    initialize_database()
    app.run()