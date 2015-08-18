import csv
import urllib
import os
from optparse import make_option

from django.core.management.base import BaseCommand
from django.utils import timezone

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
        )
    )

    def handle(self, *args, **options):
        self._mk_data_dir()

        files = self.download(period=options.get('period'),
                              states=options.get('import', 'all'),
                              force=options.get('force'))

        for csvfile in files:
            self.parse_and_save_csv(csvfile)

    @classmethod
    def parse_and_save_csv(cls, csvfile):
        with open(csvfile) as cf:
            reader = csv.DictReader(cf)
            for row in reader:
                # In file TAXRATES_ZIP5_LA201508.csv line 114 has comma in tax region name which
                # causes bad csv format, this the workaround to get combined rate
                if len(row.get(None, [])) == 1:
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

    def download(self, period='now', states='all', force=False):
        for url in self._get_taxrates_urls(period=period, states=states):
            filename = url.split('/')[-1]
            save_path = self.data_dir + '/' + filename

            if os.path.exists(save_path) and force is False:
                continue

            fn, headers = urllib.urlretrieve(url, save_path)

            if headers.dict.get('ETag') is None:
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
