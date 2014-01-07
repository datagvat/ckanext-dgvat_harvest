import datetime

from ckanext.importlib.api_command import ApiCommand
from ckanext.dgvat_harvest.dli.dliimporter import DliImporter
from ckanext.dgvat_harvest.dli.dliloader import DliLoader
from ckanclient import CkanClient

class DliLoaderCmd(ApiCommand):
    def add_options(self):
        ApiCommand.add_options(self)
        
        
    def parse_date(self, date_str):
        return datetime.date(*[int(date_chunk) for date_chunk in date_str.split('-')])
    
    def command(self):
        ApiCommand.command(self)
        data_filepaths = self.args[0]
        importer = DliImporter(filepath=data_filepaths)
        loader = DliLoader(self.client)
        loader.load_packages(importer.pkg_dict())

def load():
    DliLoaderCmd().command()
