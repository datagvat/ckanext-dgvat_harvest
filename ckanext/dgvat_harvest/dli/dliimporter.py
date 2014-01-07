# -*- coding: utf-8 -*-

from ckanext.importlib.spreadsheet_importer import XlData, SpreadsheetDataRecords, SpreadsheetPackageImporter
from ckanext.importlib.importer import RowParseError
from sqlalchemy.util import OrderedDict
import datetime
import time
import re
import logging
import os
import shutil
import uuid

log = logging.getLogger(__name__)

def map_category(cat):
   if cat == 'Arbeit':
       return 'arbeit'
   elif cat == u'BevÃ¶lkerung':
       return 'bevoelkerung'
   elif cat == 'Budget':
       return 'verwaltung-und-politik' 
   elif cat == 'Bildung und Forschung':
       return 'bildung-und-forschung'
   elif cat == 'Geographie und Planung':
       return 'geographie-und-planung'
   elif cat == 'Gesellschaft und Soziales':
       return 'gesellschaft-und-soziales'
   elif cat == 'Gesundheit':
       return 'gesundheit'
   elif cat == 'Kunst und Kultur':
       return 'kunst-und-kultur'
   elif cat == u'Ã–ffentliche Einrichtungen':
       return 'verwaltung-und-politik'    
   elif cat == 'Soziales':
       return 'gesellschaft-und-soziales'
   elif cat == 'Sport und Freizeit':
       return 'sport-und-freizeit'
   elif cat == 'Umwelt':
       return 'umwelt'
   elif cat == 'Verkehr und Technik':
       return 'verkehr-und-technik'
   elif cat == 'Verwaltung und Politik':
       return 'verwaltung-und-politik'
   elif cat == 'Wirtschaft und Tourismus':
       return 'wirtschaft-und-tourismus' 
   elif cat == 'Land- und Forstwirtschaft':
       return 'land-und-forstwirtschaft'
   elif cat == 'Finanzen und Rechnungswesen':
       return 'finanzen-und-rechnungswesen'
   else:
       return ""
   
def map_organization(org):
    if org == 'BKA':
        return 'bka'
    if org == 'BMASK':
        return 'bmask'
    if org == 'BMF':
        return 'bmf'
    if org == 'BMWF':
        return 'bmwf'
    if org == u'Gemeinde KremsmÃ¼nster':
        return 'gemeinde-kremsmuenster'
    if org == 'Land Tirol':
        return 'land-tirol'
    if org == 'Land Vorarlberg':
        return 'land-vorarlberg'
    if org == 'Stadt Graz':
        return 'stadt-graz'
    if org == 'Stadt Linz':
        return 'stadt-linz'
    if org == 'Stadt Wien':
        return 'stadt-wien'
    if org == 'Umweltbundesamt GmbH':
        return 'umweltbundesamt'
    else:
        return ''   

def map_frequency(freq):
    log.fatal('freq: #%s#' % freq)
    if freq:
        log.fatal('freq found')
        freq = freq.strip()
        if freq == u'laufend':
            return 'continual'
        elif freq == u'kontinuierlich':
            return 'continual'
        elif freq == u'taeglich':
            return 'daily'
        elif freq == u'woechentlich':
            return 'weekly'
        elif freq == u'monatlich':
            return 'monthly'        
        elif freq == u'1/4 jaehrlich':
            return 'quarterly'
        elif freq == u'1/2 jaehrlich':
            return 'biannually'
        elif freq == u'jaehrlich':
            return 'annually'   
        elif freq == u'unregelmaessig':
            return 'irregular'
        elif freq == u'nicht geplant':
            return 'not planned'
        elif freq == u'unbekannt':
            return 'unknown' 
        elif freq == u'nach Bedarf':
            log.fatal('is nach bedarf')
            return 'asNeeded'
        else: 
            return ''     
    return '' 

    

class DliImporter(SpreadsheetPackageImporter):
    usage = 'usage: %prog [options] {metadata.xls}'
    dateDots = re.compile('[0-9]{2}.[0-9]{2}.[0-9]{4}')
    dateEng = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')
    tagSplit = re.compile('[^,;]+')
    res_records = ''
    def import_into_package_records(self):
        print self._filepath
        package_data = XlData(self.log, filepath=self._filepath,
                                       buf=self._buf,
                                       sheet_index=0)
        self._package_data_records = SpreadsheetDataRecords(package_data, 'Title')
        print self._package_data_records
        package_test = XlData(self.log, filepath=self._filepath,
                                       buf=self._buf,
                                       sheet_index=1)
        self.__class__.res_records = SpreadsheetDataRecords(package_test, 'resource_url')
        shutil.move(self._filepath, self._filepath + '.' + datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f'))



    def get_by_title(self, title, default=None):
        from ckan.model.license import LicenseRegister
        from ckan.model.license import License
        
        licenseRegister = LicenseRegister()
        licenses = licenseRegister.items()        
        for i in range(len(licenses)):
            license = licenses[i][1]
            if title == unicode(license.title):
                return license.id
        else:
            return default
           
    def record_2_package(self, row_dict):
        #Date Format dd.mm.yyyy
        
        title = row_dict['Title']
        if not (title):
            raise RowParseError('Das Feld Title muss ausgefÃ¼llt werden!')
        name = title.lower()
        name = name.replace( u'Ã¤', 'ae')
        name = name.replace( u'Ã¶', 'oe')
        name = name.replace( u'Ã¼', 'ue')
        name = name.replace( u'ÃŸ', 'ss')
        name = name.replace( u' ', '-')
        name = name.replace( u':', '-')
        name = re.sub(r'[^a-zA-Z0-9 - _]', '', name)
        name = name[:99]

        license_name = row_dict.get('license')
        if(license_name == None or license_name == ''):
            license_name = u'Creative Commons Namensnennung 3.0 \xd6sterreich'
                           
        
        
        license_id = self.get_by_title(license_name, 'cc-by')
        if not license_id:
            raise RowParseError('Keine passende Lizenz gefunden: %r' % license_name)

        if not 'description' in row_dict:
            raise RowParseError('Das Feld description muss ausgefÃ¼llt werden!')

        if not 'categorization' in row_dict:
            raise RowParseError('Das Feld categorization muss ausgefÃ¼llt werden!')

        if not 'tags' in row_dict:
            raise RowParseError('Das Feld tags muss ausgefÃ¼llt werden!')

        if not 'maintainer' in row_dict:
            raise RowParseError('Das Feld maintainer muss ausgefÃ¼llt werden!')

        if not 'begin_datetime' in row_dict:
            raise RowParseError('Das Feld begin_datetime muss ausgefÃ¼llt werden!')

        begin_date = row_dict['begin_datetime']
        if begin_date <> None: 
            try:
                if begin_date.__class__ <> datetime.date:
                    begin_date = unicode(begin_date)    
                    if self.__class__.dateDots.match(begin_date):
                        begin_date = time.strptime(begin_date, "%d.%m.%Y") 
                        begin_date = time.strftime('%Y-%m-%d', begin_date)         
                    elif self.__class__.dateEng.match(begin_date):
                        begin_date = time.strptime(begin_date, "%Y-%m-%d")
                        begin_date = time.strftime('%Y-%m-%d', begin_date)     
                else:
                    begin_date = begin_date.strftime('%Y-%m-%d')
            except ValueError:
                raise RowParseError('Das Feld begin_datetime kann nicht ausgewertet werden.')
        end_date = ''
        if 'end_datetime' in row_dict:
            end_date = row_dict['end_datetime']
        
        if end_date <> None: 
            try:
                if end_date.__class__ <> datetime.date:
                    end_date = unicode(end_date)   
                    if self.__class__.dateDots.match(end_date):
                        end_date = time.strptime(end_date, "%d.%m.%Y") 
                        end_date = time.strftime('%Y-%m-%d', end_date)         
                    elif self.__class__.dateEng.match(end_date):
                        end_date = time.strptime(end_date, "%Y-%m-%d")
                        end_date = time.strftime('%Y-%m-%d', end_date)     
                else:
                    end_date = end_date.strftime('%Y-%m-%d')
            except ValueError:
                raise RowParseError('Das Feld end_datetime kann nicht ausgewertet werden.')
        
        metadata_created = ''
        if 'metadata_created' in row_dict:
            metadata_created = row_dict['metadata_created']
        
        if metadata_created <> None: 
            if metadata_created.__class__ <> datetime.date:
                metadata_created = unicode(metadata_created)   
                if self.__class__.dateDots.match(metadata_created):
                    metadata_created = time.strptime(metadata_created, "%d.%m.%Y") 
                    metadata_created = time.strftime('%Y-%m-%d', metadata_created)         
                elif self.__class__.dateEng.match(metadata_created):
                    metadata_created = time.strptime(metadata_created, "%Y-%m-%d")
                    metadata_created = time.strftime('%Y-%m-%d', metadata_created)     
            else:
                metadata_created = metadata_created.strftime('%Y-%m-%d')  
                            
        metadata_modified = ''
        if 'metadata_modified' in row_dict:
            metadata_modified = row_dict['metadata_modified']
        
        if metadata_modified <> None: 
            if metadata_modified.__class__ <> datetime.date:
                metadata_modified = unicode(metadata_modified)   
                if self.__class__.dateDots.match(metadata_modified):
                    metadata_modified = time.strptime(metadata_modified, "%d.%m.%Y") 
                    metadata_modified = time.strftime('%Y-%m-%d', metadata_modified)         
                elif self.__class__.dateEng.match(metadata_modified):
                    metadata_modified = time.strptime(metadata_modified, "%Y-%m-%d")
                    metadata_modified = time.strftime('%Y-%m-%d', metadata_modified)     
            else:
                metadata_modified = metadata_modified.strftime('%Y-%m-%d')  
        #print 'debug4importer'
        #print row_dict
        resource_dict = []
        for res_dict in self.__class__.res_records.records:
            try:
                if(res_dict['local_id'] == row_dict['local_id']):
                    res_created = ''
                    if 'resource_created' in res_dict:
                        res_created = res_dict['resource_created']
                    
                    if res_created <> None: 
                        if res_created.__class__ <> datetime.date:
                            res_created = unicode(res_created)   
                            if self.__class__.dateDots.match(res_created):
                                res_created = time.strptime(res_created, "%d.%m.%Y") 
                                res_created = time.strftime('%Y-%m-%d', res_created)         
                            elif self.__class__.dateEng.match(res_created):
                                res_created = time.strptime(res_created, "%Y-%m-%d")
                                res_created = time.strftime('%Y-%m-%d', res_created)     
                        else:
                            res_created = res_created.strftime('%Y-%m-%d')  
                                        
                    res_last_modified = ''
                    if 'resource_lastmodified' in res_dict:
                        res_last_modified = res_dict['resource_lastmodified']
                    
                    if res_last_modified <> None: 
                        if res_last_modified.__class__ <> datetime.date:
                            res_last_modified = unicode(res_last_modified)   
                            if self.__class__.dateDots.match(res_last_modified):
                                res_last_modified = time.strptime(res_last_modified, "%d.%m.%Y") 
                                res_last_modified = time.strftime('%Y-%m-%d', res_last_modified)         
                            elif self.__class__.dateEng.match(res_last_modified):
                                res_last_modified = time.strptime(res_last_modified, "%Y-%m-%d")
                                res_last_modified = time.strftime('%Y-%m-%d', res_last_modified)     
                        else:
                            res_last_modified = res_last_modified.strftime('%Y-%m-%d')  
                            
                    resource_dict.append({'url': res_dict.get('resource_url'),
                                     'format': res_dict.get('resource_format').upper(),
                                     'name': res_dict.get('resource_name'),
                                     'created': res_created,
                                     'last_modified': res_last_modified
                    })
            except RowParseError, e:
                print 'Error with row', e        
        #print resource_dict
#        print 'res: %s' % resource_dict 
        categorization = row_dict.get('categorization').split(',') 
        groups = map_organization(row_dict.get('publisher').strip())
        #print categorization
        #print 'group: %s' % groups
        #print 'dict: %s' % row_dict
        new_content = {}
        new_content['extras'] = {}
        new_content['id'] = row_dict.get('metadata_identifier') or row_dict.get('id') or str(uuid.uuid4())
        
        new_content['extras']['metadata_identifier'] = row_dict.get('metadata_identifier') or row_dict.get('id') or new_content['id']
        new_content['extras']['metadata_modified'] = metadata_modified or datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        new_content['metadata_modified'] = metadata_modified or datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        new_content['extras']['metadata_created'] = metadata_created or datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')
        new_content['maintainer'] = row_dict.get('maintainer')
        new_content['extras']['maintainer_link'] = row_dict.get('maintainer_link') or row_dict.get('maintainer_email') or ''
        new_content['download_url'] = row_dict.get('download_url')
        new_content['state'] = 'active'
        new_content['version'] = row_dict.get('version')
        new_content['license_id'] = license_id
#        new_content['resources'] = row_dict.get('resources')
#        for r in new_content['resources']:
#            if (r.get('name') != ""):
#                r['name'] = r.get('description')
#            r['format'] = r.get('format').replace('.','').upper().strip()
#            
#        if row_dict.get('tags'):
#            if not 'tags' in new_content:
#                new_content['tags'] = []
#            new_content['tags'].extend([i.strip() for i in row_dict.get('tags') if i not in omit_tags])
            
        new_content['name'] = name
        new_content['url'] = row_dict.get('url')
        new_content['notes'] = row_dict.get('description')
        new_content['title'] = row_dict.get('Title')
        new_content['extras']['update_frequency'] = map_frequency(row_dict.get('update_frequency'))
        new_content['extras']['begin_datetime'] = begin_date
        new_content['extras']['end_datetime'] = end_date
        new_content['extras']['attribute_description'] = row_dict.get('attribute_description')
        new_content['extras']['geographic_toponym'] = row_dict.get('geographic_toponym')
        new_content['extras']['geographic_bbox'] = row_dict.get('geographic_bbox')
        new_content['extras']['schema_name'] = row_dict.get('schema_name') or 'OGD Austria Metadata 2.1'
        new_content['extras']['schema_characterset'] = row_dict.get('schema_characterset') or 'utf8'
        new_content['extras']['schema_language'] = row_dict.get('schema_language') or 'ger'
        new_content['extras']['publisher'] = row_dict.get('publisher')
        new_content['extras']['publisher_email'] = row_dict.get('publisher_email')
        new_content['extras']['license_citation'] = row_dict.get('license_citation')
        new_content['extras']['lineage_quality'] = row_dict.get('lineage_quality')
        new_content['extras']['date_released'] = row_dict.get('date_released')
        new_content['extras']['en_title_and_desc'] = row_dict.get('en_title_and_desc')
        if row_dict.get('metadata_linkage'):
            new_content['extras']['metadata_linkage'] = row_dict.get('metadata_linkage')

        
        #new_content['groups'] = []
        #new_content['groups'].append('REMOVED')    
        new_content['extras']['categorization'] = []
        new_content['extras']['categorization'].extend([map_category(i) for i in categorization])
#        if row_dict.get('groups'):
#            new_content['extras']['categorization'].extend([i for i in row_dict.get('groups')])
        #print 'debug6' 
        new_content['resources'] = resource_dict
        #new_content['resources'].append(resource_dict)
        tags = []
        if row_dict.get('tags') <> None:
            tags = list(self.__class__.tagSplit.findall(unicode(row_dict.get('tags'))))
            tags.sort()
            new_content['tags'] = [t.strip() for t in tags]
        
        print 'pkg: %s' % new_content 
        return new_content