import os
from logging import getLogger

from pylons import request
from genshi.input import HTML
from genshi.filters.transform import Transformer

from ckan.plugins import implements, SingletonPlugin
from ckan.plugins import IConfigurer
from ckan.plugins import IGenshiStreamFilter
from ckan.plugins import IRoutes

log = getLogger(__name__)


class DgvatHarvest(SingletonPlugin):
    """This plugin demonstrates how a theme packaged as a CKAN
    extension might extend CKAN behaviour.

    In this case, we implement three extension interfaces:

      - ``IConfigurer`` allows us to override configuration normally
        found in the ``ini``-file.  Here we use it to specify the site
        title, and to tell CKAN to look in this package for templates
        and resources that customise the core look and feel.
        
      - ``IGenshiStreamFilter`` allows us to filter and transform the
        HTML stream just before it is rendered.  In this case we use
        it to rename "frob" to "foobar"
        
      - ``IRoutes`` allows us to add new URLs, or override existing
        URLs.  In this example we use it to override the default
        ``/register`` behaviour with a custom controller
    """
    implements(IConfigurer, inherit=True)
    implements(IGenshiStreamFilter, inherit=True)
    implements(IRoutes, inherit=True)

    def update_config(self, config):
        """This IConfigurer implementation causes CKAN to look in the
        ```public``` and ```templates``` directories present in this
        package for any customisations.

        It also shows how to set the site title here (rather than in
        the main site .ini file), and causes CKAN to use the
        customised package form defined in ``package_form.py`` in this
        directory.
        """
        pass

    def filter(self, stream):
        """Conform to IGenshiStreamFilter interface.

        This example filter renames 'frob' to 'foobar' (this string is
        found in the custom ``home/index.html`` template provided as
        part of the package).

        It also adds the chosen JQuery plugin to the page if viewing the
        dataset edit page (provides a better UX for working with tags with vocabularies)
        """
        return stream

    def before_map(self, map):
        """This IRoutes implementation overrides the standard
        ``/user/register`` behaviour with a custom controller.  You
        might instead use it to provide a completely new page, for
        example.

        Note that we have also provided a custom register form
        template at ``theme/templates/user/register.html``.
        """
        return map