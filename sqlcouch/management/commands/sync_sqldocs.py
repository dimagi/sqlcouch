import logging
from optparse import make_option
from django.core.management import BaseCommand
from django.db import transaction
import time
import signal
from sqlcouch.exceptions import NoMoreData
from sqlcouch.sync import batch_sync


class DelayedKeyboardInterrupt(object):
    def __enter__(self):
        self.signal_received = False
        self.old_handler = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.handler)

    def handler(self, signal, frame):
        self.signal_received = (signal, frame)
        logging.debug('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '-f', '--force',
            dest='force_save',
            action='store_true',
            default=False,
            help='Ignore document update conflicts and overwrite couchdocs',
        ),
        make_option(
            '-b', '--batch-size',
            dest='batch_size',
            type='int',
            default=10,
            help='Number of docs to save at a time',
        ),
        make_option(
            '-s', '--sleep-time',
            dest='sleep_time',
            type='int',
            default=1,
            help='Amount of time (in seconds) to wait between batches',
        )
    )

    def handle(self, *args, **options):
        while True:
            try:
                with DelayedKeyboardInterrupt():
                    with transaction.commit_on_success():
                        batch_sync(
                            force_save=options['force_save'],
                            limit=options['batch_size'],
                            stdout=self.stdout,
                        )
            except NoMoreData:
                self.stdout.write(
                    'Up to date! Waiting {sleep_time} '
                    'second(s) before continuing'.format(**options)
                )
                time.sleep(options['sleep_time'])
