import sys
import csv
import os
from optparse import make_option

PYTHON3 = sys.version_info > (2,)

if PYTHON3:
    from urllib.request import urlretrieve
else:
    from urllib import urlretrieve

from django.core.management.base import BaseCommand
from django.utils import timezone, version

from ...models import TaxRate


class Command(BaseCommand):
    help = 'Loads taxrates.com data'

    US_STATES = ['AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA', 'HI', 'IA', 'ID',
                 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT', 'NC',
                 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC',
                 'SD', 'TN', 'TX', 'UT', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']
    base_url = 'https://s3-us-west-2.amazonaws.com/taxrates.csv'
    app_dir = os.path.normpath(os.path.dirname(os.path.realpath(__file__)) + '/../..')
    data_dir = os.path.join(app_dir, 'data')

    # BaseCommand.option_list is deprecated in Django 1.10
    if version.get_complete_version() <= (1, 10):
        option_list = BaseCommand.option_list + (
            make_option(
                '--force', action='store_true', default=False,
                help='Import even if files are up-to-date.'
            ),
            make_option(
                '--import', metavar="DATA_TYPES", default='all',
                help='Selectively import data. Comma separated list of US states 2-alphacode'
            ),
            make_option(
                '--period', metavar="DATA_TYPES", default='now',
                help='Updated csv file for Year-Month. Eg: 201509'
            ),
            make_option(
                '--data-dir', metavar="DATA_TYPES", default=None,
                help='Data directory to store downloaded csv files'
            )

        )

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', action='store_true', default=False,
            help='Import even if files are up-to-date.'
        )
        parser.add_argument(
            '--import', metavar="DATA_TYPES", default='all',
            help=('Selectively import data. '
                  'Comma separated list of US states 2-alphacode')
        )
        parser.add_argument(
            '--period', metavar="DATA_TYPES", default='now',
            help='Updated csv file for Year-Month. Eg: 201509'
        )
        parser.add_argument(
            '--data-dir', metavar="DATA_TYPES", default=None,
            help='Data directory to store downloaded csv files'
        )

    def handle(self, *args, **options):
        self._mk_data_dir()

        files = self.download(period=options.get('period'),
                              states=options.get('import', 'all'),
                              force=options.get('force'),
                              data_dir=options.get('data_dir'))

        for csvfile in files:
            self.parse_and_save_csv(csvfile)

    @classmethod
    def parse_and_save_csv(cls, csvfile):
        with open(csvfile) as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                # In file TAXRATES_ZIP5_LA201508.csv line 114 has comma in tax region name which
                # causes bad csv format, this the workaround to get combined rate
                if len(row.get(None, [])) == 1 or 'CombinedRate' not in row:
                    row['CombinedRate'] = row['StateRate']

                fq = dict(country='US', zip_code=row['ZipCode'], state=row['State'])
                rate = float(row['CombinedRate']) * 100
                try:
                    taxrate = TaxRate.objects.get(**fq)
                    taxrate.rate = rate
                    taxrate.save(update_fields=['rate', 'updated_at'])
                except TaxRate.DoesNotExist:
                    fq.update({'tax_region_name': row['TaxRegionName'].capitalize(), 'rate': rate})
                    TaxRate.objects.create(**fq)

    def download(self, period='now', states='all', force=False, data_dir=None):
        for url in self._get_taxrates_urls(period=period, states=states):
            filename = url.split('/')[-1]
            save_path = (data_dir or self.data_dir) + '/' + filename

            if os.path.exists(save_path) and force is False:
                continue

            fn, headers = urlretrieve(url, save_path)

            if not PYTHON3:
                headers = headers.dict

            if headers.get('etag') is None:
                os.remove(save_path)
                continue

            yield save_path

    def _get_taxrates_urls(self, period='now', states='all'):
        current_ym = timezone.now().strftime('%Y%m') if period == 'now' else period
        states = states.split(',')
        states = self.US_STATES if 'all' in states else states

        for state in states:
            state = state.strip().upper()
            yield "%s/TAXRATES_ZIP5_%s%s.csv" % (self.base_url, state, current_ym)

    def _mk_data_dir(self):
        try:
            os.mkdir(self.data_dir)
        except OSError:
            pass
