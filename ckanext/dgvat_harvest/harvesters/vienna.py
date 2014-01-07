#coding: utf-8
import urllib2
import logging
import re
import HTMLParser
from hashlib import sha1
from lxml import html, etree

from ckan.lib.base import c
from ckan import model
from ckan.model import Session, Package
from ckan.logic import ValidationError, NotFound, get_action
from ckan.lib.helpers import json

from ckanext.harvest.model import HarvestObject
from ckanext.harvest.harvesters import HarvesterBase
from xml.etree.ElementTree import Element

log = logging.getLogger(__name__)

class DataWienGvAtHarvester(HarvesterBase):
    #CATALOGUE_FEED_URL = "http://data.wien.gv.at/katalog/.indexR.xml"
    config = None

    def _set_config(self,config_str):
        if config_str:
            self.config = json.loads(config_str)

            if 'api_version' in self.config:
                self.api_version = self.config['api_version']

            log.debug('Using config: %r', self.config)
        else:
            self.config = {}
            
    def validate_config(self,config):
        if not config:
            return config

        try:
            config_obj = json.loads(config)

            if 'default_tags' in config_obj:
                if not isinstance(config_obj['default_tags'],list):
                    raise ValueError('default_tags must be a list')

            if 'default_groups' in config_obj:
                if not isinstance(config_obj['default_groups'],list):
                    raise ValueError('default_groups must be a list')

                # Check if default groups exist
                context = {'model':model,'user':c.user}
                for group_name in config_obj['default_groups']:
                    try:
                        group = get_action('group_show')(context,{'id':group_name})
                    except NotFound,e:
                        raise ValueError('Default group not found')

            if 'default_extras' in config_obj:
                if not isinstance(config_obj['default_extras'],dict):
                    raise ValueError('default_extras must be a dictionary')

            if 'user' in config_obj:
                # Check if user exists
                context = {'model':model,'user':c.user}
                try:
                    user = get_action('user_show')(context,{'id':config_obj.get('user')})
                except NotFound,e:
                    raise ValueError('User not found')

            for key in ('read_only','force_all'):
                if key in config_obj:
                    if not isinstance(config_obj[key],bool):
                        raise ValueError('%s must be boolean' % key)

        except ValueError,e:
            raise e

        return config    
    
    def strip_tags(self, html):
        p = re.compile(r'<[^<]*?/?>')
        return p.sub('', html)
    
    def wrap_lists(self, html):
        h = HTMLParser.HTMLParser();
        html = html.replace('<li>', '-')
        html = html.replace('</li>', '\r\n')
        html = h.unescape(html)
        return self.strip_tags(html)
    
    def map_license(self, lic):
        if(lic == 'CC-BY-3.0'):
            return "cc-by"
        
    def map_frequency(self, freq):
        if (freq):
            if freq == 'laufend':
                return 'continual'
            elif freq == u'täglich':
                return 'daily'
            elif freq == u'wöchentlich':
                return 'weekly'
            elif freq == 'monatlich':
                return 'monthly'        
            elif freq == u'1/4 jährlich':
                return 'quarterly'
            elif freq == u'1/2 jährlich':
                return 'biannually'
            elif freq == u'jährlich':
                return 'annually'   
            elif freq == u'unregelmäßig':
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
       if cat == u'Bevölkerung':
           return 'bevoelkerung'
       elif cat == 'Kultur':
           return 'kunst-und-kultur'
       elif cat == 'Bildung':
           return 'bildung-und-forschung'
       elif cat == 'Basiskarten':
           return 'geographie-und-planung'
       elif cat == 'Gesundheit':
           return 'gesundheit'
       elif cat == 'Freizeit':
           return 'sport-und-freizeit'
       elif cat == 'Soziales':
           return 'gesellschaft-und-soziales'
       elif cat == 'Umwelt':
           return 'umwelt'
       elif cat == 'Arbeit':
           return 'arbeit'
       elif cat == 'Verkehr':
           return 'verkehr-und-technik'
       elif cat == 'Budget':
           return 'verwaltung-und-politik' 
       elif cat == 'Verwaltungseinheiten':
           return 'verwaltung-und-politik'
       elif cat == u'Öffentliche Einrichtungen':
           return 'verwaltung-und-politik'    
       elif cat == 'Wirtschaft':
           return 'wirtschaft-und-tourismus' 
       else:
           return ""

    def info(self):
        return {
            'name': 'data_wien_gv_at',
            'title': 'Open Government Data Wien',
            'description': 'Special HTML - Import from data.wien.gv.at'
        }

    def gather_stage(self, harvest_job):
        log.debug('In DataWienGvAt gather_stage')
        
#        proxy_handler = urllib2.ProxyHandler({'http': 'http://IP-Address removed'})
#        opener = urllib2.build_opener(proxy_handler)
#        urllib2.install_opener(opener)


        #p = etree.XMLParser(no_network=False)
        f = urllib2.urlopen(harvest_job.source.url)
        doc = etree.parse(f)
        ids = []
        for link in doc.findall("//item/link"):
            link = link.text
            id = sha1(link).hexdigest()
            obj = HarvestObject(guid=id, job=harvest_job, content=link)
            obj.save()
            ids.append(obj.id)
        return ids

    def fetch_stage(self, harvest_object):
#        proxy_handler = urllib2.ProxyHandler({'http': 'http://IP-Address removed'})
#        opener = urllib2.build_opener(proxy_handler)
#        urllib2.install_opener(opener)
        f = urllib2.urlopen(harvest_object.content)
        
        doc = html.parse(f)
        package_dict = {'extras': {'harvest_dataset_url': harvest_object.content},
                        'resources': []}
        package_dict['title'] = doc.findtext('//title').split(' | ')[0]
        if not doc.find('//table[@class="BDE-table-frame vie-ogd-table"]'):
            return False
        for meta in doc.findall("//meta"):
            key = meta.get('name')
            value = meta.get('content')
            if key is None or value is None:
                continue
            if key == 'DC.Creator':
                package_dict['author'] = value
            elif key == 'DC.date.created':
                package_dict['metadata_created'] = value
            elif key == 'DC.date.modified':
                package_dict['metadata_modified'] = value
        for row in doc.findall('//table[@class="BDE-table-frame vie-ogd-table"]//tr'):
            key = row.find('th/p').text
            elem = row.find('td')
            if key == 'Beschreibung':
                package_dict['notes'] = elem.xpath("string()")
            elif key == 'Bezugsebene':
                package_dict['extras']['geographic_coverage'] = elem.xpath("string()")
            elif key == 'Zeitraum':
                package_dict['extras']['temporal_coverage'] = elem.xpath("string()")
            elif key == 'Aktualisierung':
                package_dict['extras']['temporal_granularity'] = elem.xpath("string()")
            elif key == 'Kategorien': 
                categories = elem.xpath("string()").split(',')
                package_dict['extras']['categories'] = [c.strip() for c in categories]
            elif key == 'Typ': 
                package_dict['extras']['type'] = elem.xpath("string()")
            elif key == u'Attribute':
                elem.tag = 'span'
                package_dict['extras']['attributes'] = self.wrap_lists(etree.tostring(elem))
            elif key == u'Datenqualität':
                package_dict['extras']['data_quality'] = elem.xpath("string()")
            elif key == 'Kontakt':
                package_dict['maintainer'] = elem.xpath("string()")
            elif key == 'Lizenz':
                if 'by/3.0/at/deed.de' in elem.findall('.//a')[0].get('href'):
                    package_dict['license_id'] = 'cc-by'
            elif key == 'Schlagworte':
               tagString = elem.xpath("string()").replace(';', ',')
               tags = tagString.split(',')
               package_dict['tags'] = [unicode(self.strip_tags(t).strip().replace(' ', '_').encode('latin-1'), 'ISO-8859-1') for t in tags]
               package_dict['tags'] = [t.replace('(', '').replace(')', '') for t in package_dict['tags']]
            elif key == 'Datensatz':
                for li in elem.findall('.//li'):
                    l = li.findall('.//a')
                    if len(l) > 0:
                        link = l[0].get('href')
                    else:
                        link = ''
                    if li.find('.//abbr') is not None:
                        res = {'description': li.xpath('string()'),
                               'url': link,
                               'format': li.find('.//abbr').text}
                        package_dict['resources'].append(res)
                    else:
                        package_dict['url'] = link

        harvest_object.content = json.dumps(package_dict)
        harvest_object.save()
        return True

    def import_stage(self,harvest_object):
        omit_tags = ['ogd', 'None']
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id,harvest_object,'Import')
            return False
        
        self._set_config(harvest_object.job.source.config)

        try:
            old_content = json.loads(harvest_object.content)
            
            new_content = {}
            new_content['id'] = harvest_object.guid

            # Common extras
            new_content['extras'] = {}
            #new_content['extras']['harvest_catalogue_name'] = u'Open Government Data Wien'
            #new_content['extras']['harvest_catalogue_url'] = u'http://data.wien.gv.at'
            
            
            new_content['maintainer'] = old_content.get('maintainer')
            new_content['maintainer_email'] = ''
            new_content['author'] = old_content.get('maintainer')
            new_content['resources'] = old_content.get('resources')
            for r in new_content['resources']:
                if (r.get('name') != ""):
                    r['name'] = r.get('description') 
            
            if old_content.get('tags'):
                if not 'tags' in new_content:
                    new_content['tags'] = []
                new_content['tags'].extend([i for i in old_content.get('tags') if i not in omit_tags])
                
                
            new_content['name'] = 'ogdwien_' + self._gen_new_name(old_content.get('title'))
            if(len(new_content['name']) > 100):
                new_content['name'] = new_content['name'][:99]
                                            
            new_content['license_id'] = 'cc-by'
            new_content['url'] = old_content.get('extras').get('harvest_dataset_url')
            new_content['notes'] = old_content.get('notes')
            new_content['title'] = old_content.get('title')
            frq = self.map_frequency(old_content.get('extras').get('temporal_granularity'))
            if (frq != ''):
                new_content['extras']['update_frequency'] = frq
                log.info("update_frequency: %s" % frq)
                
            temp = old_content.get('extras').get('temporal_coverage')
            if (temp):
                regex = re.compile("[0-9][0-9]+")
                r = regex.search(temp)
                if (r):
                    new_content['extras']['begin_datetime'] = temp
                     
            new_content['extras']['attribute_description'] = old_content.get('extras').get('attributes')
            new_content['extras']['geographic_toponym'] = old_content.get('extras').get('geographic_coverage')
            new_content['extras']['remote_id'] = harvest_object.guid
            new_content['extras']['remote_guid'] = old_content.get('title')
            new_content['extras']['publisher'] = 'OGD Wien'
            new_content['extras']['publisher_email'] = 'open@post.wien.gv.at'
            new_content['groups'] = []
            for cat in old_content.get('extras').get('categories'):
                ng = self.map_category(cat)
                if (ng != ''):
                    new_content['groups'].append(ng)
                log.info('Group: %s - %s' % (cat, ng) )      
            
            

            if self.config:
                # Set default tags if needed
                default_tags = self.config.get('default_tags',[])
                if default_tags:
                    if not 'tags' in new_content:
                        new_content['tags'] = []
                    new_content['tags'].extend([t for t in default_tags if t not in new_content['tags']])
    
                # Set default groups if needed
                default_groups = self.config.get('default_groups',[])
                if default_groups:
                    if not 'groups' in new_content:
                        new_content['groups'] = []
                    new_content['groups'].extend([g for g in default_groups if g not in new_content['groups']])
                
            result= self._create_or_update_package(new_content, harvest_object)
            
            if result and self.config.get('read_only',False) == True:

                package = model.Package.get(new_content['id'])

                # Clear default permissions
                model.clear_user_roles(package)

                # Setup harvest user as admin
                user_name = self.config.get('user',u'harvest')
                user = model.User.get(user_name)
                pkg_role = model.PackageRole(package=package, user=user, role=model.Role.ADMIN)

                # Other users can only read
                for user_name in (u'visitor',u'logged_in'):
                    user = model.User.get(user_name)
                    pkg_role = model.PackageRole(package=package, user=user, role=model.Role.READER)
        
            return result
        
        except Exception, e:
            log.exception(e)
            self._save_object_error('%r' % e, harvest_object, 'Import')

