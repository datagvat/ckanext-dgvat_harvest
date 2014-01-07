from setuptools import setup, find_packages
import sys, os


version = '0.9.7c'


setup(
	name='ckanext-dgvat_harvest',
	version=version,
	description="data.gv.at Plugin for harvesting",
	long_description="""\
	""",
	classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
	keywords='',
	author='BRZ GesmbH',
	author_email='data@brz.gv.at',
	url='www.brz.gv.at',
	license='GPL',
	packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
	namespace_packages=['ckanext', 'ckanext.dgvat_harvest'],
	include_package_data=True,
	package_data={'ckan': ['i18n/*/LC_MESSAGES/*.mo']},
	zip_safe=False,
	install_requires=[
		# -*- Extra requirements: -*-
	],
	entry_points=\
	"""
        [ckan.plugins]
        datagvat_harvest=ckanext.dgvat_harvest.plugin:DgvatHarvest
        data_wien_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataWienGvAtHarvester
		data_linz_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataLinzGvAtHarvester
		data_graz_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataGrazGvAtHarvester
		data_noe_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataNoeGvAtHarvester
		data_ooe_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataOoeGvAtHarvester
		data_ktn_gv_at_harvester=ckanext.dgvat_harvest.harvesters:DataKtnGvAtHarvester
		excel_harvester=ckanext.dgvat_harvest.harvesters:ExcelHarvester
		
	    [console_scripts]
	    dli = ckanext.dgvat_harvest.dli:load
	# Add plugins here, eg
	# myplugin=ckanext.dgvat_harvest:PluginClass
	""",
)
