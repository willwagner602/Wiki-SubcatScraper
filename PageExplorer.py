__author__ = 'wwagner'

from WikipediaScraper import get_page

href = 'https://commons.wikimedia.org/wiki/File:F-16_Fighting_Falcon_Laage1.jpg'

page = get_page(href)

possible_licenses = [('table', 'licensetpl_wrapper'),
                     ('table', 'layouttemplate licensetpl'),
                     ('table', 'layouttemplate licensetpl mw-content-ltr'),
                     ('table', 'layouttemplate mw-content-ltr')]

license_table = possible_licenses[0]
full_license = ' '.join(page.find([license_table[0], license_table[1]]).text.split())
cc2_text = 'This file is licensed under the Creative Commons'
short_license = full_license[full_license.find('licensed under the') + 19:full_license.find('license.') + 8]
print(short_license)