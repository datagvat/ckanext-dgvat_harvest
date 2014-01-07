#coding: utf-8
import urllib2
import logging
import re
import HTMLParser
import uuid

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

from ckanext.dgvat_harvest.dli.dliimporter import DliImporter

log = logging.getLogger(__name__)

class ExcelHarvester(HarvesterBase):
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
            elif freq == 'kontinuierlich':
                return 'continual'
            elif freq == 'taeglich':
                return 'daily'
            elif freq == 'woechentlich':
                return 'weekly'
            elif freq == 'monatlich':
                return 'monthly'        
            elif freq == '1/4 jaehrlich':
                return 'quarterly'
            elif freq == '1/2 jaehrlich':
                return 'biannually'
            elif freq == 'jaehrlich':
                return 'annually'   
            elif freq == 'unregelmaessig':
                return 'irregular'
            elif freq == 'nicht geplant':
                return 'not planned'
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
            'name': 'xlsImport',
            'title': 'ExcelImporter',
            'description': 'Excel Importer'
        }

    def gather_stage(self, harvest_job):
        log.debug('In Excel Importer gather_stage')
        
#        proxy_handler = urllib2.ProxyHandler({'http': 'http://IP-Address removed'})
#        opener = urllib2.build_opener(proxy_handler)
#        urllib2.install_opener(opener)


        #p = etree.XMLParser(no_network=False)
        
        data_filepaths = harvest_job.source.url        
        ids = []
        importer = DliImporter(filepath=data_filepaths)
        cnt=0
        print importer.pkg_dict()
        for pkg  in importer.pkg_dict():
            id = sha1(data_filepaths + str(cnt)).hexdigest()
            cnt=cnt+1
            obj = HarvestObject(guid=id, job=harvest_job, content=json.dumps(pkg))
            obj.save()
            ids.append(obj.id)
        return ids

    def fetch_stage(self, harvest_object):
#        proxy_handler = urllib2.ProxyHandler({'http': 'http://IP-Address removed'})
#        opener = urllib2.build_opener(proxy_handler)
#        urllib2.install_opener(opener)

        #harvest_object.content =
        #harvest_object.content = json.dumps(pckg)
        harvest_object.save()
        return True

    def import_stage(self,harvest_object):
        
        if not harvest_object:
            log.error('No harvest object received')
            return False

        if harvest_object.content is None:
            self._save_object_error('Empty content for object %s' % harvest_object.id,harvest_object,'Import')
            return False
        
        self._set_config(harvest_object.job.source.config)
        print self.config
        try:
            content = json.loads(harvest_object.content)
            content['id'] = content.get('id') or harvest_object.guid
            
            default_groups = self.config.get('group',[])
            if default_groups:
                if not 'groups' in content:
                    content['groups'] = []
                content['groups'].extend([g for g in default_groups if g not in content['groups']])
                
            prefix = self.config.get('prefix')
            if prefix:
                if not content['name'].startswith(prefix):
                    content['name'] = prefix + content['name']
            
            print "content: %s" % content
            result = self._create_or_update_package(content, harvest_object)
#            if result and self.config.get('read_only',False) == True:
#
#                package = model.Package.get(content['id'])
#
#                # Clear default permissions
#                model.clear_user_roles(package)
#
#                # Setup harvest user as admin
#                user_name = self.config.get('user',u'admin')
#                user = model.User.get(user_name)
#                pkg_role = model.PackageRole(package=package, user=user, role=model.Role.ADMIN)
#
#                # Other users can only read
#                for user_name in (u'visitor',u'logged_in'):
#                    user = model.User.get(user_name)
#                    pkg_role = model.PackageRole(package=package, user=user, role=model.Role.READER)
#            
#            #return false
            return result
        except Exception, e:
            log.exception(e)
            self._save_object_error('%r' % e, harvest_object, 'Import')

