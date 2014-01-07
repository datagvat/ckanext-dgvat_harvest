#coding: utf-8
import logging

from ckan import model
from ckan.model import Session
from ckan.logic.action.update import package_update_rest
from ckan.logic.action.get import package_show
from ckan.lib.helpers import json

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester

log = logging.getLogger(__name__)

class DataGrazGvAtHarvester(CKANHarvester):

    def info(self):
        return {
            'name': 'ckan_graz',
            'title': 'CKAN (Graz) neu',
            'description': 'CKAN Harvester modified for importing ckan-data from data.graz.gv.at',
            'form_config_interface':'Text' 
        }
        
    def map_license(self, lic):
        if(lic == 'CC-BY-3.0'):
            return "cc-by"
        
    def map_frequency(self, freq):
        if (freq):
            freq = freq.encode('latin-1')
            if freq == 'laufend':
                return 'continual'
            elif freq == 't\u00e4glich':
                return 'daily'
            elif freq == 'w\u00f6chentlich':
                return 'weekly'
            elif freq == 'monatlich':
                return 'monthly'        
            elif freq == 'quartalsweise':
                return 'quarterly'
            elif freq == '1/2 j\u00e4hrlich':
                return 'biannually'
            elif freq == 'j\u00e4hrlich':
                return 'annually'   
            elif freq == 'j\xe4hrlich':
                return 'annually'    
            elif freq == 'unregelm\u00e4\u00dfig':
                return 'irregular'
            elif freq == 'nicht geplant':
                return 'notPlanned'
            elif freq == 'unbekannt':
                return 'unknown'
            elif freq == 'nach Bedarf':
                return 'asNeeded'            
            else: 
                return ''     
        return ''                        
       
       

    def import_stage(self,harvest_object):
        omit_tags = ['ogd', 'none']
        

        old_content = json.loads(harvest_object.content)
        
        new_content = {}
        new_content['extras'] = {}
        
        new_content['id'] = old_content.get('id')
        
        new_content['extras']['metadata_identifier'] = old_content.get('extras').get('metadata_identifier') or old_content.get('id') or ''
        new_content['extras']['metadata_modified'] = old_content.get('extras').get('metadata_modified') or old_content.get('metadata_modified') or ''
        #new_content['extras']['metadata_created'] = old_content.get('metadata_created') or ''    

        new_content['maintainer'] = old_content.get('maintainer')
        new_content['extras']['maintainer_link'] = old_content.get('extras').get('Kontaktseite der datenverantwortlichen Stelle') or old_content.get('maintainer_email') or ''
        new_content['download_url'] = old_content.get('download_url')
        new_content['state'] = old_content.get('state')
        new_content['version'] = old_content.get('version')
        new_content['license_id'] = self.map_license(old_content.get('license_id'))
        new_content['resources'] = old_content.get('resources')
        for r in new_content['resources']:
            if (r.get('name') != ""):
                r['name'] = r.get('description')
            r['format'] = r.get('format').replace('.','').upper().strip()
            
        if old_content.get('tags'):
            if not 'tags' in new_content:
                new_content['tags'] = []
            new_content['tags'].extend([i.strip() for i in old_content.get('tags') if i not in omit_tags])
            
        new_content['name'] = 'ogdgraz_' + old_content.get('name')
        new_content['url'] = old_content.get('url').strip()
        new_content['notes'] = old_content.get('notes').strip()
        new_content['title'] = old_content.get('title').strip()
        frq = self.map_frequency(old_content.get('extras').get('Aktualisierungszyklus'))
        if (frq != ''):
            new_content['extras']['update_frequency'] = frq
            log.info("update_frequency: %s" % frq)
        new_content['extras']['begin_datetime'] = old_content.get('extras').get('Zeitliche Ausdehnung (Anfang)')
        new_content['extras']['end_datetime'] = old_content.get('extras').get('Zeitliche Ausdehnung (Ende)')
        new_content['extras']['attribute_description'] = old_content.get('extras').get('Attributbeschreibung')
        new_content['extras']['geographic_toponym'] = old_content.get('extras').get('Geographische Bezugsebene')
        new_content['extras']['geographic_bbox'] = old_content.get('extras').get('Geographische Ausdehnung')
        new_content['extras']['schema_name'] = 'OGD Austria Metadata 2.1'
        new_content['extras']['schema_characterset'] = old_content.get('extras').get('Character Set Code des Metadatensatzes')
        new_content['extras']['schema_language'] = old_content.get('extras').get('Sprache des Metadatensatzes')
        new_content['extras']['publisher'] = 'Stadt Graz'
        new_content['extras']['publisher_email'] = 'ogd@stadt.graz.at'
        new_content['extras']['license_citation'] = old_content.get('extras').get('Datenquelle')
        new_content['extras']['lineage_quality'] = old_content.get('Datenqualit\u00e4t')
        new_content['extras']['date_released'] = old_content.get('Ver\u00f6ffentlichungsdatum')
        new_content['extras']['en_title_and_desc'] = old_content.get('Titel und Beschreibung Englisch')
        
        
        new_content['groups'] = []
        new_content['groups'].append('fdedbd18-1dab-46be-b356-71278176c27c')    
        
        new_content['extras']['categorization'] = []
        if old_content.get('groups'):
            new_content['extras']['categorization'].extend([i for i in old_content.get('groups')])
        
        
        harvest_object.content = json.dumps(new_content)
        log.fatal(new_content) 
        
#        context = {
#            'model': model,
#            'session': Session,
#            'user': user_name,
#            'api_version': api_version,
#            'schema': schema,
#        }        
#        
#        data_dict['name_or_id'] = new_content['name']
#        existing_package_dict = get_action('package_show')(context, data_dict)
#        log.fatal(existing_package_dict)
        super(DataGrazGvAtHarvester, self).import_stage(harvest_object)
        
#        if harvest_object.package_id:
##            # Add some extras to the newly created package
##            new_extras = {
##                'eu_country': self.config.get('eu_country',''),
##                'harvest_catalogue_name': self.config.get('harvest_catalogue_name',''),
##                'harvest_catalogue_url': harvest_object.job.source.url,
##                'harvest_dataset_url': harvest_object.job.source.url.strip('/') + '/package/' + harvest_object.package_id,
##            }
##
#            context = {
#                'model': model,
#                'session': Session,
#                'user': u'harvest_graz',
#                'id': harvest_object.package_id
#            }
#                
#            
#            package_update_rest(data_dict,context)

