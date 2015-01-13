#!/usr/bin/env python
"""
Data models for CDR mapping.
"""

import cPickle
import os
import sqlite3
import string


__author__ = "Dan O'Day"
__license__ = "MIT"
__version__ = "0.1"
__maintainer__ = "Dan O'Day"
__email__ = "d@4n68r.com"
__status__ = "Prototype"


class Database(object):
    """
    Database object.
    """
    def __init__(self):
        self.database_filename = os.path.join(os.path.dirname(__file__), 'cdr_data.db')

    def __str__(self):
        return self.database_filename

    def __repr__(self):
        return 'Database()'

    def create_tables(self):
        """
        Create database tables needed by CDRMapper
        """
        conn = sqlite3.connect(self.database_filename)
        cur = conn.cursor()

        cur.execute("""
            create table TOLLS_CASE (
              Case_ID integer primary key autoincrement not null,
              Case_Number varchar not null,
              Case_Agency varchar not null,
              Case_Agent varchar not null,
              Case_Analyst varchar not null,
              Case_Target_Number varchar not null
            );
        """)

        conn.commit()

        cur.execute("""
            create table TOWER (
              Tower_ID integer primary key autoincrement not null,
              Tower_Case_ID integer not null,
              Tower_Cell_Site_ID varchar not null,
              Tower_Latitude varchar not null,
              Tower_Longitude varchar not null,
              Tower_Sector varchar not null,
              Tower_Azimuth integer not null
            );
        """)

        conn.commit()

        cur.execute("""
            create table CDR (
              CDR_ID integer primary key autoincrement not null,
              CDR_Case_ID integer not null,
              CDR_Called_Number varchar not null,
              CDR_Cell_Site_ID varchar not null,
              CDR_Sector varchar not null,
              CDR_Other blob null
            );
        """)

        conn.commit()
        conn.close()


class TollsCase(object):
    """
    Case object for tolls case.
    """
    def __init__(self, case_number, agency, agent, analyst, target_number):
        self.case_number = case_number
        self.agency = agency
        self.agent = agent
        self.analyst = analyst
        self.target_number = target_number
        self.case_unique_id = None

    def __str__(self):
        return ''.join(('Case: ', self.case_number, ' (', self.agency, ')'))

    def __repr__(self):
        return ''.join(('TollsCase(',
                        repr(self.case_number), ', ',
                        repr(self.agency), ', ',
                        repr(self.agent), ', ',
                        repr(self.analyst), ', ',
                        repr(self.target_number), ')'))

    def save(self):
        """
        Saves TollsCase object to database.
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        cur = conn.execute("""insert into TOLLS_CASE (
                                Case_Number, Case_Agency, Case_Agent, Case_Analyst, Case_Target_Number
                              )
                              values (?, ?, ?, ?, ?);""", (self.case_number, self.agency, self.agent, self.analyst,
                                                           self.target_number))
        conn.commit()
        self.case_unique_id = int(cur.lastrowid)  # set unique case id to primary key int value from db
        conn.close()

    @staticmethod
    def get_case_number(pk):
        """
        Returns case number given primary key of TollsCase record
        :param pk: primary key of TollsCase record
        :return: case number as string
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row

        cur = conn.execute("select Case_Number from TOLLS_CASE where Case_ID=?", (pk,))
        case_number = cur.fetchone()[0]

        conn.close()
        return case_number

    @staticmethod
    def get_case_details(pk):
        """
        Gets details of TollsCase given primary key
        :param pk: primary key of TollsCase record
        :return: dictionary containing TollsCase fields
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row

        cur = conn.execute("select * from TOLLS_CASE where Case_ID=?", (pk,))
        record = cur.fetchone()

        conn.close()
        return {
            'Case Number': record['Case_Number'],
            'Agency': record['Case_Agency'],
            'Agent': record['Case_Agent'],
            'Analyst': record['Case_Analyst'],
            'Target Number': record['Case_Target_Number']
        }


class Tower(object):
    """
    Cell site / tower object.
    """
    def __init__(self, tolls_case_id, cell_site_id, latitude, longitude, sector, azimuth):
        self.case_id = int(tolls_case_id)  # TollsCase object case_unique_id property
        self.cell_site_id = cell_site_id
        self.latitude = latitude
        self.longitude = longitude
        self.sector = sector
        self.azimuth = azimuth

    def __str__(self):
        return ''.join(('Tower: ', self.cell_site_id, ' (Sector: ', self.sector, ', Azimuth: ', self.azimuth, ')'))

    def __repr__(self):
        return ''.join(('Tower(',
                        repr(self.cell_site_id), ', ',
                        repr(self.latitude), ', ',
                        repr(self.longitude), ', ',
                        repr(self.sector), ', ',
                        repr(self.azimuth), ')'))

    def save(self):
        """
        Saves Tower object to database.
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        cur = conn.execute("""
            insert into TOWER (Tower_Case_ID, Tower_Cell_Site_ID, Tower_Latitude, Tower_Longitude, Tower_Sector,
            Tower_Azimuth) values (?, ?, ?, ?, ?, ?);""", (self.case_id, self.cell_site_id, self.latitude,
                                                           self.longitude, self.sector, self.azimuth))
        conn.commit()
        conn.close()

    @staticmethod
    def get_tower_location(case_id, cell_site_id, sector):
        """
        Gets location of cell site (tower) given necessary CDR data.
        :param case_id: Primary key of TollsCase object (case_unique_id)
        :param cell_site_id: Cell site / tower identifier
        :param sector: Sector of cell site / tower connected to
        :return: Dictionary containing latitude, longitude of tower and azimuth of tower sector connected to
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row
        cur = conn.execute("""
            select Tower_Latitude, Tower_Longitude, Tower_Azimuth
            from TOWER
            where Tower_Case_ID=?
              and Tower_Cell_Site_ID=?
              and Tower_Sector=?;""", (case_id, cell_site_id, sector))
        record = cur.fetchone()
        conn.close()
        return {
            'Latitude': record['Tower_Latitude'],
            'Longitude': record['Tower_Longitude'],
            'Azimuth': record['Tower_Azimuth']
        }


class CDR(object):
    """
    Call Detail Record (CDR) object
    """
    def __init__(self, tolls_case_id, called_number, cell_site_id, sector, other_fields):
        self.case_id = int(tolls_case_id)  # TollsCase object case_unique_id property
        self.called_number = called_number
        self.cell_site_id = cell_site_id
        self.sector = sector
        self.other_fields = other_fields
        self.cdr_unique_id = None

    def __str__(self):
        if self.cdr_unique_id:
            return ''.join(('CDR #', self.cdr_unique_id))
        else:
            return 'CDR (Unsaved)'

    def __repr__(self):
        return ''.join(('CDR(',
                        repr(self.case_id), ', ',
                        repr(self.called_number), ', ',
                        repr(self.cell_site_id), ', ',
                        repr(self.sector), ', ',
                        repr(self.other_fields), ')'))

    def save(self):
        """
        Saves CDR object to database.
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        cur = conn.execute("""
            insert into CDR (CDR_Case_ID, CDR_Called_Number, CDR_Cell_Site_ID, CDR_Sector, CDR_Other) values
            (?, ?, ?, ?, ?);""", (self.case_id, self.called_number, self.cell_site_id, self.sector,
                                  sqlite3.Binary(cPickle.dumps(self.other_fields, cPickle.HIGHEST_PROTOCOL))))
        conn.commit()
        self.cdr_unique_id = int(cur.lastrowid)  # set unique cdr id to primary key int value from db
        conn.close()

    @staticmethod
    def get_cdr_details(pk, case_id):
        """
        Gets details of CDR given primary key
        :param pk: primary key of CDR record
        :param case_id: primary key of TollsCase object (case_unique_id)
        :return: dictionary containing CDR fields
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row

        cur = conn.execute("select * from CDR where CDR_ID=? and CDR_Case_ID=?", (pk, case_id))
        record = cur.fetchone()

        conn.close()
        return {
            'Case ID': record['CDR_Case_ID'],
            'Called Number': record['CDR_Called_Number'],
            'Cell Site ID': record['CDR_Cell_Site_ID'],
            'Sector': record['CDR_Sector'],
            'Other Fields:': dict(cPickle.loads(str(record['CDR_Other'])))
        }

    @staticmethod
    def get_cdrs_with_location_data(case_id):
        """
        Gets primary keys of CDRs with location data (i.e. they have a specified cell site / tower ID)
        :param case_id: TollsCase primary key
        :return: list of primary keys of CDR records with location data
        """
        db = Database()
        conn = sqlite3.connect(db.database_filename)
        conn.text_factory = str
        conn.row_factory = sqlite3.Row

        cur = conn.execute("""
            select CDR_ID
            from CDR
            where CDR_Case_ID=?
              and CDR_Cell_Site_ID != ''
              and CDR_Cell_Site_ID is not null
            order by CDR_ID;""", (case_id,))
        records = cur.fetchall()
        conn.close()

        return [row[0] for row in records]

    @staticmethod
    def generate_cdata(pk, case_id):
        """
        Generates CDATA (XML Character Data) that pops up in description of points on the map
        :param pk: primary key of CDR record
        :param case_id: primary key of TollsCase object (case_unique_id)
        :return: CDATA as string (including header and footer CDATA tags)
        """
        cdr_details = CDR.get_cdr_details(pk, case_id)
        tower_details = Tower.get_tower_location(case_id, cdr_details['Cell Site ID'], cdr_details['Sector'])
        cdata = """
        <![CDATA[ <table border='0' cellspacing='0' cellpadding='0'>
            <tr>
                <td colspan='2' style='vertical-align: top; padding-left: 10px; padding-right: 10px; white-space: nowrap;'>
                    <b>{cdr_id}</b>
                </td>
            </tr>
            <tr>
                <td colspan='2' style='vertical-align: top; padding-left: 10px; padding-right: 10px; max-width: 400px; white-space: nowrap;'>
                    &nbsp;
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Calling Number</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {callingnum}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Called Number</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {callednum}
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Dialed Number</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {dialed}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Call Direction</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {direction}
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Start Date</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {start}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>End Date</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {end}
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Duration</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {duration}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Cell Site</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {cellsite}
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Sector</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {sector}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Azimuth</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {azimuth}
                </td>
            </tr>
            <tr bgcolor='#ddffdd' >
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Latitude</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {latitude}
                </td>
            </tr>
            <tr>
                <td style='vertical-align: top; padding-left: 10px; white-space: nowrap;'>
                    <b>Longitude</b>
                </td>
                <td style='vertical-align: top; padding-left: 6px; padding-right: 10px; white-space: nowrap;'>
                    {longitude}
                </td>
            </tr>
        </table> ]]>""".format(cdr_id=str(pk),
                               callingnum=Report.xml_safe(cdr_details['Calling Number']),
                               callednum=Report.xml_safe(cdr_details['Called Number']),
                               dialed=Report.xml_safe(cdr_details['Dialed Digits']),
                               direction=Report.xml_safe(cdr_details['Call Direction']),
                               start=Report.xml_safe(cdr_details['Start Date']),
                               end=Report.xml_safe(cdr_details['End Date']),
                               duration=Report.xml_safe(cdr_details['Duration']),
                               cellsite=Report.xml_safe(cdr_details['Cell Site ID']),
                               sector=Report.xml_safe(cdr_details['Sector']),
                               azimuth=Report.xml_safe(tower_details['Azimuth']),
                               latitude=Report.xml_safe(tower_details['Latitude']),
                               longitude=Report.xml_safe(tower_details['Longitude']))
        return cdata


class Report(object):
    """
    Report object which combines data from multiple sources.
    """
    def __init__(self, case_id, report_path):
        self.case_id = case_id
        self.report_path = report_path
        self.report_name = self.get_report_name()

    def __str__(self):
        return 'Report object for case ID #', self.case_id

    def __repr__(self):
        return ''.join(('Report(', repr(self.case_id), ')'))

    def get_report_name(self):
        """
        Ensures case number can be used in file name without problematic characters
        :return: file name of map/report with .kml extension
        """
        valid_chars = "-%s%s" % (string.ascii_letters, string.digits)
        case_number = TollsCase.get_case_number(self.case_id)
        fn = ''.join([c for c in case_number if c in valid_chars])
        return ''.join([fn, '.kml'])

    def generate_map(self):
        """
        Generates kml map file, linking tower and CDR data as needed
        :return: file name of map file
        """
        case_details = TollsCase.get_case_details(self.case_id)
        kml_header = """
        <?xml version="1.0" encoding="UTF-8" ?>
        <kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2">
            <Document>
                <name>{casenum} ({agency}) :: {targetnum}</name>
                <Snippet maxLines="1">
                    <![CDATA[ {casenum} ]]>
                </Snippet>
                <open>1</open>
                <Style>
                    <IconStyle>
                        <Icon />
                    </IconStyle>
                    <BalloonStyle>
                        <text>
                            <![CDATA[ $[description] ]]>
                        </text>
                    </BalloonStyle>
                </Style>
                <description>
                    <![CDATA[ {casenum} ({agency}) location data for target number {targetnum}.
                    Prepared for {agent} by {analyst}. ]]>
                </description>
                <StyleMap id="Map1">
                    <Pair>
                        <key>normal</key>
                        <styleUrl>#NormalMap1</styleUrl>
                    </Pair>
                    <Pair>
                        <key>highlight</key>
                        <styleUrl>#HighlightMap1</styleUrl>
                    </Pair>
                </StyleMap>
                <Style id="NormalMap1">
                    <IconStyle>
                        <scale>1</scale>
                        <Icon>
                            <href>http://maps.google.com/mapfiles/kml/paddle/ylw-blank.png</href>
                        </Icon>
                        <color>FF00FFFF</color>
                    </IconStyle>
                    <LabelStyle>
                        <color>FFFFFFFF</color>
                        <scale>1</scale>
                    </LabelStyle>
                    <LineStyle>
                        <color>FFFF00FF</color>
                        <width>2</width>
                    </LineStyle>
                    <PolyStyle>
                        <fill>0</fill>
                        <outline>1</outline>
                        <color>00FF00FF</color>
                    </PolyStyle>
                    <BalloonStyle>
                        <text>
                            <![CDATA[ $[description] ]]>
                        </text>
                    </BalloonStyle>
                </Style>
                <Style id="HighlightMap1">
                    <IconStyle>
                        <scale>1.1</scale>
                        <Icon>
                            <href>http://maps.google.com/mapfiles/kml/paddle/ylw-blank.png</href>
                        </Icon>
                        <color>FF00FFFF</color>
                    </IconStyle>
                    <LabelStyle>
                        <color>FFFFFFFF</color>
                        <scale>1.1</scale>
                    </LabelStyle>
                    <LineStyle>
                        <color>FFFF00FF</color>
                        <width>3</width>
                    </LineStyle>
                    <PolyStyle>
                        <fill>0</fill>
                        <outline>1</outline>
                        <color>70FF00FF</color>
                    </PolyStyle>
                    <BalloonStyle>
                        <text>
                            <![CDATA[ $[description] ]]>
                        </text>
                    </BalloonStyle>
                </Style>""".format(casenum=self.xml_safe(case_details['Case Number']),
                                   targetnum=self.xml_safe(case_details['Target Number']),
                                   agency=self.xml_safe(case_details['Agency']),
                                   agent=self.xml_safe(case_details['Agent']),
                                   analyst=self.xml_safe(case_details['Analyst']))
        kml_footer = """
            </Document>
        </kml>"""

        cdrs_with_location_data = CDR.get_cdrs_with_location_data(self.case_id)

        with open(os.path.join(self.report_path, self.report_name), 'wb') as f:
            f.write(self.strip_whitespace(kml_header))

            for cdr_id in cdrs_with_location_data:
                cdr_details = CDR.get_cdr_details(cdr_id, self.case_id)
                tower_details = Tower.get_tower_location(self.case_id,
                                                         cdr_details['Cell Site ID'],
                                                         cdr_details['Sector'])
                # not an essential feature -- for future expansion
                # timespan_data = ''
                # if cdr_details['Start Date'] and cdr_details['Start Date'].strip() != '' and cdr_details['End Date'] \
                #         and cdr_details['End Date'].strip() != '':
                #     timespan_data = """
                #     <TimeSpan>
                #         <begin>2013-06-15T09:20:00Z</begin>
                #         <end>2013-06-15T09:31:00Z</end>
                #     </TimeSpan>"""

                placemark_data = """
                <Placemark>
                    <name><![CDATA[ {pk} ]]></name>
                    <Snippet maxLines="0" />
                    <styleUrl>#Map1</styleUrl>
                    <ExtendedData />
                    <LookAt>
                        <longitude>{longitude}</longitude>
                        <latitude>{latitude}</latitude>
                        <range>1000</range>
                        <altitudeMode>relativeToGround</altitudeMode>
                        <tilt>0</tilt>
                        <heading>0</heading>
                    </LookAt>
                    <Point>
                        <altitudeMode>clampToGround</altitudeMode>
                        <extrude>0</extrude>
                        <coordinates>{longitude},{latitude},0</coordinates>
                    </Point>
                    <description>
                        {description}
                    </description>
                </Placemark>""".format(pk=cdr_id,
                                       longitude=self.xml_safe(tower_details['Longitude']),
                                       latitude=self.xml_safe(tower_details['Latitude']),
                                       description=CDR.generate_cdata(cdr_id, self.case_id))

                f.write(self.strip_whitespace(placemark_data))

            f.write(self.strip_whitespace(kml_footer))

        return self.report_name

    @staticmethod
    def strip_whitespace(s):
        """
        Removes excess newlines, tabs, and spaces from XML for smaller file size
        :param s: string to be cleaned up
        :return: cleaned up string
        """
        return ' '.join(s.split())

    @staticmethod
    def xml_safe(s):
        """
        Makes a string xml-safe
        :param s: string
        :return: xml-safe string
        """
        unsafe = {
            '"': '&quot;',
            "'": '&apos;',
            "<": '&lt;',
            ">": '&gt;',
            "&": '&amp;'
        }

        s = str(s).strip().replace('\r', '').replace('\n', '')

        return ''.join(unsafe.get(c, c) for c in s)