#coding: utf-8
import logging

from ckan import model
from ckan.model import Session
from ckan.logic.action.update import package_update_rest
from ckan.logic.action.get import package_show
from ckan.lib.helpers import json
from ckan.lib.munge import munge_title_to_name

from ckanext.harvest.harvesters.ckanharvester import CKANHarvester
import ckanext.dgvat_por.lib.dgvat_helper as helper

from ckanext.harvest.model import HarvestJob, HarvestObject, HarvestGatherError, \
                                    HarvestObjectError

log = logging.getLogger(__name__)

class DataNoeGvAtHarvester(CKANHarvester):
    
    def _gen_new_name(self,title):
        '''
        Creates a URL friendly name from a title
        '''
        name = munge_title_to_name(title).replace('_', '-')
        while '--' in name:
            name = name.replace('--', '-')
        return name

    def info(self):
        return {
            'name': 'custom_noe',
            'title': 'Custom API Import (NOE)',
            'description': 'CKAN Harvester modified for importing data from noe.gv.at',
            'form_config_interface':'Text'
        }
        
        
    def gather_stage(self,harvest_job):
        log.debug('In NOEHarvester gather_stage (%s)' % harvest_job.source.url)
        
        package_ids = []

        self._set_config(harvest_job.source.config)
        
        # Get source URL
        base_url = harvest_job.source.url.rstrip('/')
        
        # Check if previous jobs exist and when they took place
        previous_job = Session.query(HarvestJob) \
                        .filter(HarvestJob.source==harvest_job.source) \
                        .filter(HarvestJob.gather_finished!=None) \
                        .filter(HarvestJob.id!=harvest_job.id) \
                        .order_by(HarvestJob.gather_finished.desc()) \
                        .limit(1).first()
        if (previous_job and not previous_job.gather_errors and not len(previous_job.objects) == 0):
            if not self.config.get('force_all',False):
                get_all_packages = False
    
                # Request only the packages modified since last harvest job
                last_time = harvest_job.gather_started.strftime("%d.%m.%Y")
                url = base_url + '/search/%s' % last_time
            else:
                url = base_url
        else:
            # Request all remote packages
            url = base_url + '/search'
        log.debug("url: %s" % url) 
        try:
            content = self._get_content(url)
        except Exception,e:
            self._save_gather_error('Unable to get content for URL: %s: %s' % (url, str(e)),harvest_job)
            return None

        package_ids = json.loads(content)

        try:
            object_ids = []
            if len(package_ids):
                for package_id in package_ids:
                    # Create a new HarvestObject for this identifier
                    obj = HarvestObject(guid = package_id, job = harvest_job)
                    obj.save()
                    object_ids.append(obj.id)

                return object_ids

            else:
               self._save_gather_error('No packages received for URL: %s' % url,
                       harvest_job)
               return None
        except Exception, e:
            self._save_gather_error('%r'%e.message,harvest_job)
    
        
    def fetch_stage(self,harvest_object):
        log.debug('In NOEHarvester fetch_stage')

        self._set_config(harvest_object.job.source.config)

        # Get source URL
        url = harvest_object.source.url.rstrip('/')
        url = url + '/json/' + harvest_object.guid

        # Get contents
        try:
            content = self._get_content(url)
        except Exception,e:
            self._save_object_error('Unable to get content for package: %s: %r' % \
                                        (url, e),harvest_object)
            return None

        # Save the fetched contents in the HarvestObject
        harvest_object.content = content
        harvest_object.save()
        return True


    def import_stage(self,harvest_object):
        omit_tags = ['ogd', 'none']
        

        old_content = json.loads(harvest_object.content)
        old = json.loads(harvest_object.content)

        
        new_content = {}
        
        new_content = old_content
        
        new_content['id'] = old_content.get('extras').get('metadata_identifier') or old_content.get('id')
        new_content['license_id'] = 'cc-by'
        new_content['name'] = self._gen_new_name(old_content.get('title'))
        new_content['metadata_modified'] = old_content.get('extras').get('metadata_modified') or old_content.get('metadata_modified') or ''
        new_content['extras']['publisher'] = u'Land Niederösterreich'
        new_content['resources'] = []
        if isinstance(old.get('resources'), list):
            new_content['resources'] = old.get('resources')
        else:
            new_content['resources'].append(old.get('resources'))
        new_content['tags']= []
        if isinstance(old.get('tags'), list):
            new_content['tags'] = old.get('tags')
        else:
            new_content['tags'].append(old.get('tags'))


        harvest_object.content = json.dumps(new_content)
        print harvest_object
        super(DataNoeGvAtHarvester, self).import_stage(harvest_object)
        
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

#

