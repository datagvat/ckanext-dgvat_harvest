#coding: utf-8
import logging

from ckan import model
from ckan.model import Session
from ckan.logic.action.update import package_update_rest
from ckan.logic.action.get import package_show
from ckan.lib.helpers import json

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester

log = logging.getLogger(__name__)

class DataLinzGvAtHarvester(CKANHarvester):

    def info(self):
        return {
            'name': 'ckan_linz',
            'title': 'CKAN (Linz)',
            'description': 'CKAN Harvester modified for importing ckan-data from data.linz.gv.at',
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
            elif freq == '1/4 j\u00e4hrlich':
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
        
    def map_category(self, cat):
        catList = cat.split('/')
        for c in catList:
            c = c.strip()
            if catList[0] == 'population':
                return 'bevoelkerung'
            elif catList[0] == 'kultur':
                return 'kunst-und-kultur'
            elif catList[0] == 'geodaten':
                return 'geographie-und-planung'
            elif catList[0] == 'gesundheit':
                return 'gesundheit'
            elif catList[0] == 'gkk':
                return 'gesundheit'            
            elif catList[0] == 'freizeit':
                return 'sport-und-freizeit'
            elif catList[0] == 'soziales_gesellschaft':
                return 'gesellschaft-und-soziales'
            elif catList[0] == 'umwelt':
                return 'umwelt'
            elif catList[0] == 'arbeit':
                return 'arbeit'
            elif catList[0] == 'verkehr':
                return 'verkehr-und-technik'
            elif catList[0] == 'linz_ag':
                return 'verkehr-und-technik'       
            elif catList[0] == 'politik_verwaltung':
                if catList[1] == 'finanzen':
                    return 'finanzen-und-rechnungswesen'
                return 'verwaltung-und-politik'
            elif catList[0] == 'linz_service':
                return 'verwaltung-und-politik'    
            elif catList[0] == 'linz-service':
                return 'verwaltung-und-politik'
            elif catList[0] == 'stadt':
                return 'geographie-und-planung'             
            elif catList[0] == 'wirtschaft':
                if catList[1] == 'arbeitslose':
                    return 'arbeit'
                return 'wirtschaft-und-tourismus' 
            elif catList[0] == 'tourismus':
                return 'wirtschaft-und-tourismus'
            elif catList[0] == 'stadt':
                return 'geographie-und-planung'
       
       

    def import_stage(self,harvest_object):
        omit_tags = ['ogd', 'none']
        

        old_content = json.loads(harvest_object.content)
        
        new_content = {}
        new_content['extras'] = {}
        
        new_content['id'] = old_content.get('id')
        
        new_content['extras']['metadata_identifier'] = old_content.get('extras').get('metadata_identifier') or old_content.get('id')
        new_content['extras']['metadata_modified'] = old_content.get('extras').get('metadata_modified') or old_content.get('metadata_modified') or ''
        new_content['metadata_modified'] = old_content.get('extras').get('metadata_modified') or old_content.get('metadata_modified') or ''

        new_content['maintainer'] = old_content.get('author').strip()
        new_content['extras']['maintainer_link'] = old_content.get('extras').get('Kontaktseite der datenverantwortlichen Stelle') or old_content.get('maintainer_email')
        new_content['download_url'] = old_content.get('download_url')
        new_content['state'] = old_content.get('state')
        new_content['version'] = old_content.get('version')
        new_content['license_id'] = self.map_license(old_content.get('license_id'))
        new_content['metadata_created'] = old_content['metadata_created']
        
        new_content['resources'] = old_content.get('resources')
        for r in new_content['resources']:
            if (r.get('name') != ""):
                r['name'] = r.get('description')
            r['format'] = r.get('format').replace('.','').upper().strip()
            
        if old_content.get('tags'):
            if not 'tags' in new_content:
                new_content['tags'] = []
            new_content['tags'].extend([i.strip() for i in old_content.get('tags') if i not in omit_tags])
            
        new_content['name'] = old_content.get('name')
        new_content['url'] = old_content.get('url').strip()
        new_content['notes'] = old_content.get('notes').strip()
        new_content['title'] = old_content.get('title').strip()
        frq = self.map_frequency(old_content.get('extras').get('Aktualisierungszyklus'))
        if (frq != ''):
            new_content['extras']['update_frequency'] = frq
            log.info("update_frequency: %s" % frq)
            
        new_content['extras']['begin_datetime'] = old_content.get('extras').get('Zeitliche Ausdehnung (Anfang)') or old_content.get('extras').get('Zeitliche Ausdehnung (Anfang)\t')
        new_content['extras']['end_datetime'] = old_content.get('extras').get('Zeitliche Ausdehnung (Ende)') or old_content.get('extras').get('Zeitliche Ausdehnung (Ende)\t')
        new_content['extras']['attribute_description'] = old_content.get('extras').get('Wiki-Link')
        new_content['extras']['geographic_toponym'] = old_content.get('extras').get('Geographische Bezugsebene')
        new_content['extras']['geographic_bbox'] = old_content.get('extras').get('Minimum bounding rectangle')
        new_content['extras']['schema_name'] = old_content.get('extras').get('Bezeicheichung der Metadatenstruktur')
        new_content['extras']['schema_characterset'] = 'utf-8'
        new_content['extras']['schema_language'] = old_content.get('extras').get('Sprache des Metadatensatzes')
        new_content['extras']['publisher'] = 'Stadt Linz'
        new_content['extras']['publisher_email'] = old_content.get('maintainer_email')
        new_content['extras']['license_citation'] = old_content.get('extras').get('Datenquelle')
        
        new_content['extras']['categorization'] = []
        c = old_content.get('extras').get('Kategorie')
        cat = self.map_category(c)
        log.info("categorie: '%s' - %s'" % (c,cat))
        if (cat != ''):
            new_content['extras']['categorization'].append(cat)
            
        
        
        harvest_object.content = json.dumps(new_content)
        print harvest_object
        super(DataLinzGvAtHarvester, self).import_stage(harvest_object)
        
#        if harvest_object.package_id:
#            # Add some extras to the newly created package
#            new_extras = {
#                'eu_country': self.config.get('eu_country',''),
#                'harvest_catalogue_name': self.config.get('harvest_catalogue_name',''),
#                'harvest_catalogue_url': harvest_object.job.source.url,
#                'harvest_dataset_url': harvest_object.job.source.url.strip('/') + '/package/' + harvest_object.package_id,
#            }
#
#            context = {
#                'model': model,
#                'session': Session,
#                'user': u'harvest',
#                'id': harvest_object.package_id
#            }
#            
#            data_dict = {'extras':new_extras}
#            
#            package_update_rest(data_dict,context)

