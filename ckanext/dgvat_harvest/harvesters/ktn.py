#coding: utf-8
import logging

from ckan import model
from ckan.model import Session
from ckan.logic.action.update import package_update_rest
from ckan.logic.action.get import package_show
from ckan.lib.helpers import json
import ckanext.dgvat_por.lib.dgvat_helper as dgvathelper

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester

log = logging.getLogger(__name__)

class DataKtnGvAtHarvester(CKANHarvester):

    def info(self):
        return {
            'name': 'ckan_ktn',
            'title': 'CKAN (Kaernten) neu',
            'description': 'CKAN Harvester modified for importing ckan-data from data.ktn.gv.at',
            'form_config_interface':'Text' 
        }
        
    def import_stage(self,harvest_object):
        omit_tags = ['ogd', 'none']
        

        old_content = json.loads(harvest_object.content)
        
        new_content = json.loads(harvest_object.content)
        new_content['license_id'] = dgvathelper.map_license(old_content.get('license_id'))

        new_content['name'] = 'land-ktn_' + old_content.get('name')
        frq = dgvathelper.map_update_frequency(old_content.get('extras').get('update_frequency'))
        if (frq != ''):
            print frq
            new_content['extras']['update_frequency'] = frq
            log.info('update_frequency: %s' % frq)
        new_content['extras']['publisher'] = u'Land Kärnten'

        new_content['groups'] = []
        
        harvest_object.content = json.dumps(new_content)
        log.fatal(new_content) 
        
        super(DataKtnGvAtHarvester, self).import_stage(harvest_object)
