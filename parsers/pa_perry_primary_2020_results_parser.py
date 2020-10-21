import os
import csv
from parsers.pa_pdf_parser import PDFStringIterator, PDFPageIterator

COUNTY = 'PERRY'

OUTPUT_FILE = os.path.join('..', '2020', '20200602__pa__primary__perry__precinct.csv')
OUTPUT_HEADER = ['county', 'precinct', 'office', 'district', 'party', 'candidate',
                 'election_day', 'absentee', 'provisional', 'military', 'votes']

# To create a v2 file, open the existing file in Acrobat and save as the below filename.
# This action is needed because the provided file is version 1.4, but the parser only
# supports 1.5 and greater
PERRY_FILE = os.path.join('..', '..', 'openelections-sources-pa', '2020',
                          'Perry PA Primary county-election-results-1 v2.pdf')
PAGE_HEADER = [
    'County Elections Results',
    'Perry County PA, PA_Perry_2020P, Jun 02, 2020',
    'All Precincts, All Districts, All Counter Groups, All ScanStations, All Contests, All Boxes',
    'Total Ballots Cast: 11262, Registered Voters: 24587, Overall Turnout: 45.80%',
    '31 precincts reported out of 31 total',
    '2020-06-05',
    '13:07:51',
    'Choice',
    'Votes',
    'Vote %',
    'AB',
    'ED',
    'MI',
    'PR'
]

PRECINCT_PREFIX = 'Precinct '
PAGE_FOOTER_PREFIX = 'Page: '
LAST_ROW_CANDIDATE = 'Total'
VOTE_HEADER = ['votes', None, 'absentee', 'election_day', 'military', 'provisional']

RAW_OFFICE_TO_OFFICE_AND_DISTRICT = {
    'Congress 12': ('U.S. House', 12),
    'PA Senator 15': ('State Senate', 15),
    'PA Rep 86': ('General Assembly', 86),
}


class PerryPDFPageParser:
    def __init__(self, page, continued_table_header, continued_precinct):
        self._string_iterator = PDFStringIterator(page.get_strings())
        self._validate_and_skip_page_header()
        self._continued_table_header = continued_table_header
        self._continued_precinct = continued_precinct

    def __iter__(self):
        while not self._page_is_done():
            self._precinct = self._get_precinct()
            while not self._precinct_is_done() and not self._page_is_done():
                yield from self._iterate_precinct_data()

    def get_continued_table_header(self):
        return self._table_header

    def get_continued_precinct(self):
        return self._precinct

    def _iterate_precinct_data(self):
        self._table_header = self._get_table_header()
        office, district, party = self._extract_office_district_and_party()
        for row in self._iterate_office_data():
            row.update(office=office, district=district, party=party)
            if self._row_is_valid(row):
                yield row

    def _iterate_office_data(self):
        while self._table_header and not self._page_is_done():
            candidate = self._get_candidate()
            row = {'county': COUNTY, 'precinct': self._precinct, 'candidate': candidate}
            self._populate_vote_data(row)
            if candidate == LAST_ROW_CANDIDATE:
                self._table_header = None
            yield row

    def _populate_vote_data(self, row):
        for vote_type in VOTE_HEADER:
            vote_count = next(self._string_iterator)
            if vote_type:
                row[vote_type] = int(vote_count)

    def _get_precinct(self):
        precinct = None
        if self._continued_precinct:
            precinct = self._continued_precinct
            self._continued_precinct = None
        if self._precinct_is_done():
            precinct = next(self._string_iterator)
            _, precinct = precinct.split(PRECINCT_PREFIX)
        assert precinct
        return precinct

    def _get_table_header(self):
        if self._continued_table_header:
            table_header = self._continued_table_header
            self._continued_table_header = None
            return table_header
        return next(self._string_iterator)

    def _get_candidate(self):
        candidate = next(self._string_iterator).title()
        if candidate.startswith('Write-In'):
            candidate = 'Write-In'
        return candidate

    def _extract_office_district_and_party(self):
        office, party = self._table_header.split(' (', 1)
        _, office = office.split(' ', 1)
        party, _ = party.split(')', 1)
        assert party in ['REP', 'DEM']
        district = ''
        if office in RAW_OFFICE_TO_OFFICE_AND_DISTRICT:
            office, district = RAW_OFFICE_TO_OFFICE_AND_DISTRICT[office]
        return office, district, party

    def _validate_and_skip_page_header(self):
        assert [next(self._string_iterator) for _ in range(len(PAGE_HEADER))] == PAGE_HEADER

    def _page_is_done(self):
        return self._string_iterator.peek().startswith(PAGE_FOOTER_PREFIX)

    def _precinct_is_done(self):
        return self._string_iterator.peek().startswith(PRECINCT_PREFIX)

    @staticmethod
    def _row_is_valid(row):
        if 'Delegate' in row['office']:
            return False
        if 'COMMITTEE' in row['office']:
            return False
        if row['candidate'] == LAST_ROW_CANDIDATE:
            return False
        return True


def pdf_to_csv(pdf, csv_writer):
    csv_writer.writeheader()
    previous_table_header = None
    previous_precinct = None
    for page in pdf:
        print(f'processing page {page.get_page_number()}')
        pdf_page_parser = PerryPDFPageParser(page, previous_table_header, previous_precinct)
        for row in pdf_page_parser:
            csv_writer.writerow(row)
        previous_table_header = pdf_page_parser.get_continued_table_header()
        previous_precinct = pdf_page_parser.get_continued_precinct()


if __name__ == "__main__":
    with open(OUTPUT_FILE, 'w', newline='') as f:
        pdf_to_csv(PDFPageIterator(PERRY_FILE),
                   csv.DictWriter(f, OUTPUT_HEADER))