#!/opt/homebrew/bin/python3
#!/opt/local/bin/python
#!/opt/anaconda3/bin/python

import re
import os
import string
import argparse



class DumpBlock:
    def __init__(self, type='text', name=''):
        # all start out this way
        self.type = type
        self.files = {}
        self.subtype = ''
        self.properties = {}
        self.context = {}
        self.text = []
        self.start_line = 0

    def add_line (self, line):
        self.text.append (line)

    def first_line (self):
        line = ''
        if (len (self.text) > 0):
            line = self.text[0]
        return line

    def has_lines (self):
        return len (self.text) > 0

    def dump(self, position=0, level=0):
        print ()
        print ('vvvvvvvvvvvv ', position, '; start line ', self.start_line, '; ', end = '')
        print ('types: ' + self.type + '/' + self.subtype + ', properties: ', end = '')
        print (self.properties, ', context: ', self.context)
        for line in self.text:
            print (line)
        print ('-- files')
        for file in self.files.keys():
            #print (self.files[file])
            print ('    ', file, ' (', len(self.files[file]), ')')
        print ('^^^^^^^^^^^^ ', position)

class DumpFile:

    def __init__(self, text, type):
        self.text = []
        self.type = ''

class DumpBlocks:

    def __init__(self):
        self.blocks = []
    
    def add_line (self, line, line_number):
        #print ('line (', line, ')!\n')
        if line == '===========================================================================' or line == ' =================================================================':
            #print ('bingo (', line, ')!\n')
            self.blocks.append (DumpBlock('subsep'))
            self.blocks[-1].start_line = line_number
        elif line == '###########################################################################' or line == ' ###########################################################################':
            #print ('bango (', line, ')!\n')
            self.blocks.append (DumpBlock('sep'))
            self.blocks[-1].start_line = line_number
        elif line == '%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%' or line == ' %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%':
            #print ('bongo (', line, ')!\n')
            self.blocks.append (DumpBlock('bigsep'))
            self.blocks[-1].start_line = line_number
        else:
            if not self.blocks[0] or self.blocks[-1].type != 'text':
                self.blocks.append (DumpBlock ('text'))
                self.blocks[-1].start_line = line_number
            
        self.blocks[-1].add_line (line)

    def len(self):
        return len (self.blocks) #self.blocks.size()

    def dump(self):
        i = 0;
        for block in self.blocks:
            block.dump(i)
            i += 1

    # match the type_sequence, starting at block start_at, up to end_at, return first block number of first match, or -1 on no match
    def find_type_sequence (self, type_sequence=[], start_at=0, end_at=9999999):
        type_count = len (type_sequence)
        if type_count < 1:
            return -1
        # this is the absolute max
        last_start = len (self.blocks) - type_count
        if start_at > last_start:
            return -1
        if (end_at < last_start): 
            last_start = end_at
        for i in range (start_at, last_start+1):
            match = 1
            for j in range (0, type_count):
                if type_sequence[j] != self.blocks[i+j].type:
                    match = 0
                    break
            if (match):
                return (i)
        return -1

    # parse out properties from main section text
    def set_section_properties (self, section):
        for line in section.text:
            key_val = re.split (r':\s+', line)
            if (len (key_val) != 2):
                continue
            key = self.safer_name (key_val[0])
            value = key_val[1]
            section.properties[key] = value

    def get_line_key_values (self, line, properties):
        pairs = line.split (', ')
        for pair in pairs:
            key, value = pair.split (': ')
            properties[key.lower()] = value
            

    # absorb text from next block then remove it
    def absorb_following_block (self, block_number):
        self.blocks[block_number].text.extend (self.blocks[block_number+1].text)
        self.blocks[block_number+1 : block_number+2] = []
        

    # find the main sections
    def create_sections (self):
        while ((section_start := self.find_type_sequence (['bigsep', 'text', 'bigsep'])) >= 0):
            section = self.blocks[section_start+1]
            section.type = 'section'
            if (section.text[0].startswith ('Report Time')):
                section.type = 'dump'
            elif (section.text[0].startswith ('Hostname:')):
                section.type = 'host'
            self.set_section_properties (section)
            self.blocks[section_start:section_start+3] = [section]

    def config_file_subsection (self, line):
        return re.fullmatch (r'(server|groups|databases|assignments|hosts|clusters|keystore|kms|tokenizer|mimetypes)(_[0-9])?\.xml', line)

    # find the secondary sections
    def create_subsections_recursive (self, start_at=0):
        subsection_titles = {
            'Host Status': True,
            'App Server Status': True,
            'Database Topology': True,
            'Forest Status': True,
            'Trigger Definitions': True,
            'CPF Domains': True,
            'CPF Pipelines': True,
            'FlexRep Domains': True,
            'SQL Schemas': True,
            'SQL Views': True,
            'XML Schemas': True,
            'Configuration': True,
        }
        
        if ((subsection_start := self.find_type_sequence (['subsep', 'text', 'subsep'], start_at)) >= 0):
            text_block = self.blocks[subsection_start+1]
            #print ('check: ', text_block.text[0], '->', subsection_titles.get (text_block.text[0], 'nil'))
            if self.config_file_subsection (text_block.first_line()):
                subsection = self.blocks[subsection_start+1]
                subsection.type = 'config_file'
                subsection.properties['filename'] = subsection.text[0]
                self.blocks[subsection_start:subsection_start+3] = [subsection]
                self.create_subsections (subsection_start+1)
            elif subsection_titles.get (text_block.first_line(), False):
                subsection = self.blocks[subsection_start+1]
                subsection.type = 'subsection'
                self.blocks[subsection_start:subsection_start+3] = [subsection]
                self.create_subsections (subsection_start+1)
            else:
                self.create_subsections (subsection_start+1)

    # find the secondary sections
    def create_subsections (self):
        subsection_titles = {
            'Host Status': True,
            'App Server Status': True,
            'Database Topology': True,
            'Forest Status': True,
            'Trigger Definitions': True,
            'CPF Domains': True,
            'CPF Pipelines': True,
            'FlexRep Domains': True,
            'SQL Schemas': True,
            'SQL Views': True,
            'XML Schemas': True,
            'Configuration': True,
        }

        start_at = 0
        
        while ((subsection_start := self.find_type_sequence (['subsep', 'text', 'subsep'], start_at)) >= 0):
            text_block = self.blocks[subsection_start+1]
            #print ('check: ', text_block.text[0], '->', subsection_titles.get (text_block.text[0], 'nil'))
            if self.config_file_subsection (text_block.first_line()):
                subsection = self.blocks[subsection_start+1]
                subsection.type = 'config_file'
                subsection.properties['filename'] = subsection.text[0]
                self.blocks[subsection_start:subsection_start+3] = [subsection]
            elif subsection_titles.get (text_block.first_line(), False):
                subsection = self.blocks[subsection_start+1]
                subsection.type = 'subsection'
                self.blocks[subsection_start:subsection_start+3] = [subsection]
            start_at = subsection_start+1



    # put this together from its bits
    def reconstitute_database_topology (self):
        found = 0
        block_number = 0
        while block_number < len (self.blocks):
            block = self.blocks[block_number]
            if block.type == 'subsection' and block.text[0] == 'Database Topology':
                block.subtype = 'database_topology'
                block.text = []
                found = 1
                break
            block_number += 1
        if found:
            while block_number < len (self.blocks) and self.blocks[block_number+1].type != 'subsection':
                blocks.absorb_following_block (block_number)

    
    # remove notices that a file isn't there (dump checks for all older versions)
    def remove_missing_configurations (self):
        block_number = 0
        while block_number < len (self.blocks):
            if self.find_type_sequence (['subsep', 'text', 'subsep'], block_number, block_number) >= 0\
                and re.fullmatch ('Configuration file .* does not exist.', self.blocks[block_number+1].text[0]):
                    self.blocks[block_number : block_number+3] = []
            else:
                block_number += 1

    def safer_name (self, string=''):
        return string.lower().translate (str.maketrans (' ', '_'))

    def remove_block_number (self, block_number):
        if len(self.blocks) > block_number+1:  self.blocks[block_number:block_number+1] = []

    # remove notices that a file isn't there (checks for all older versions)
    def context_run_through (self):
        block_number = 1
        context = {}
        while block_number < len (self.blocks):
            block = self.blocks[block_number]
            last_block = self.blocks[block_number-1]

            # get rid of leading blank lines in text blocks
            if block.type == 'text':
                while block.has_lines() and re.fullmatch (r'\s*', block.text[0]):
                    block.text[0:1] = []

            # update from preceding block
            if last_block.type == 'dump':
                context['type'] = last_block.type
                context['host'] = last_block.properties['report_host']
            elif last_block.type == 'host':
                context['type'] = last_block.type
                context['host'] = last_block.properties['hostname']
            elif last_block.type == 'subsection':
                # database_topology already set
                if not last_block.subtype:
                    last_block.subtype = self.safer_name (last_block.text[0])
                context['type'] = last_block.type
                context['subtype'] = last_block.subtype
            #elif block.type == 'text':

            # update from this block
            # 
            #  appserver status
            if  context['type'] == 'subsection' and context['subtype'] == 'app_server_status' and block.text[0].startswith ('Group: '):
                block.type = 'appserver'
                self.get_line_key_values (block.text[0], block.properties)
                context['group'] = block.properties['group']
                block.text[0 : 1] = []
            #  triggers, first line is db
            elif context['type'] == 'subsection' and context['subtype'] == 'host_status' and block.type == 'text':
                if block.has_lines():
                    block.type = 'host_status'
            elif context['type'] == 'subsection' and context['subtype'] == 'trigger_definitions' and block.type == 'text':
                if block.has_lines():
                    block.type = 'triggers'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'cpf_domains' and block.type == 'text':
                if block.has_lines():
                    block.type = 'cpf_domain'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'cpf_pipelines' and block.type == 'text':
                if block.has_lines():
                    block.type = 'cpf_pipelines'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'flexrep_domains' and block.type == 'text':
                if block.has_lines():
                    block.type = 'flexrep_domains'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'sql_schemas' and block.type == 'text':
                if block.has_lines():
                    block.type = 'sql_schemas'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'sql_views' and block.type == 'text':
                if block.has_lines():
                    block.type = 'sql_views'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'xml_schemas' and block.type == 'text':
                if block.has_lines():
                    block.type = 'xml_schemas'
                    block.properties['database'] = block.text[0]
                    block.text[0 : 1] = []
            elif context['type'] == 'subsection' and context['subtype'] == 'forest_status' and block.type == 'text':
                if block.has_lines():
                    block.type = 'forest_status'
                    block.properties['database'] = block.first_line()
                    block.text[0 : 1] = []
                
            block.context = context.copy()
            block_number += 1

    def has_block_number (self, block_number=-1):
        if block_number >= 0 and block_number < len(self.blocks):
            return True
        return False

    # remove notices that a file isn't there (checks for all older versions)
    def setup_config_files (self):
        block_number = -1
        while (block_number := block_number + 1) < len (self.blocks):
            block = self.blocks[block_number]
            if block.type == 'config_file' and self.has_block_number (block_number):
                next_block = self.blocks[block_number+1]
                if next_block.type == 'subsep':
                    self.remove_block_number(block_number+1)
                next_block = self.blocks[block_number+1]
                if next_block.type == 'text' and next_block.first_line().startswith ('Validation results: '):
                    block.properties['validation_results'] = next_block.first_line()[len ('Validation results: '):]
                    self.remove_block_number(block_number+1)
                next_block = self.blocks[block_number+1]
                if next_block.type == 'subsep':
                    self.remove_block_number(block_number+1)
                next_block = self.blocks[block_number+1]
                if next_block.type == 'text':
                    block.text = next_block.text
                    self.remove_block_number(block_number+1)

    def get_check_xml (self, block):
        # print ('checking block type: ' + block.type)
        lines = block.text
        current_element = '---';
        current_file = [];
        line_count = 0
        file_number = 1
        for line in lines:
            line_count += 1
            m = re.match(r'\s*<(/?)([^>\s]+)', line)
            if m:
                end_slash, element_name = m.group(1), m.group(2)
                #print ('   match ' + end_slash + element_name)
                if end_slash:
                    # end element
                    if current_element == element_name:
                        # nice, matched up
                        #print ('< obai ' + element_name)
                        filename = element_name
                        if block.type == 'config_file':  filename = block.properties['filename']
                        elif block.type == 'xml_schemas':  filename = f'Schema-{file_number}'
                        elif block.type == 'host_status':  filename = element_name.title() + '.xml'
                        current_file.append (line)
                        if not element_name in block.files:
                            block.files[filename] = []
                        block.files[filename].append (current_file)
                        current_element = '---';
                        current_file = [];
                        file_number += 1
                    else:
                        current_file.append (line)
                else:
                    # start element
                    if current_element == '---':
                        #print ('> ohai ' + element_name)
                        current_file = [line]
                        current_element = element_name
                    else:
                        current_file.append (line)
            elif current_file == '---': 
                print ('ERROR: unowned line at about line ', block.start_line+line_count)
            elif current_file != '---': 
                current_file.append (line)

    def get_check_xml_blocks (self):
        for block in self.blocks:
            if block.type == 'appserver':
                # TODO better check of needed properties for path
                if 'group' in block.properties:
                    self.get_check_xml (block)
            #elif block.type == 'forest_status' or block.type == 'triggers' or block.type == 'cpf_domain' or block.type == 'cpf_pipelines':
            elif block.type in ['forest_status', 'triggers', 'cpf_domain', 'cpf_pipelines', 'flexrep_domains', 'xml_schemas', 'sql_schemas', 'sql_views']:
                # TODO better check of needed properties for path
                if 'database' in block.properties:
                    self.get_check_xml (block)
            elif block.type == 'config_file':
                # TODO better check of needed properties for path
                if 'host' in block.context:
                    self.get_check_xml (block)
            elif block.type == 'host_status':
                # TODO better check of needed properties for path
                if 'host' in block.context:
                    self.get_check_xml (block)

    def write_file (self, path, filename, lines):
        os.makedirs (path, 0o777, True)
        filepath = path + '/' + filename
        with open(filepath, 'w') as f:
            for line in lines:
                f.write (line + '\n')

    def write_files (self):
        for block in self.blocks:
            if block.type == 'dump':
                self.write_file ('Support-Dump', 'Support-Request.txt', block.text)
                block.properties['written'] = True
            elif block.subtype == 'database_topology':
                self.write_file ('Support-Dump', 'Database-Topology.txt', block.text)
                block.properties['written'] = True
            elif block.type == 'config_file':
                # TODO better check of needed properties for path
                # Support-Dump/_group_/_host_/Configuration/_filename_
                if 'group' in block.context:
                    path = 'Support-Dump/' + block.context['group'] + '/' + block.context['host'] + '/Configuration'
                    for filekey in block.files.keys():
                        self.write_file (path, filekey, block.files[filekey][0])
                    block.properties['written'] = True
            elif block.type == 'appserver':
                # TODO better check of needed properties for path
                # Support-Dump/Default/prodrlmkg01/App-Servers/App-Services-Status.xml
                if 'group' in block.context:
                    path = 'Support-Dump/' + block.context['group'] + '/' + block.properties['host'] + '/App-Servers'
                    filename = block.properties['appserver'] + '-Status.xml'
                    for filekey in block.files.keys():
                        # filename matches files key how (in general)?
                        self.write_file (path, filename, block.files[filekey][0])
                    block.properties['written'] = True
            elif block.type == 'host_status':
                # TODO better check of needed properties for path
                # Support-Dump/Default/prodrlmkg01/App-Servers/App-Services-Status.xml
                if 'group' in block.context:
                    path = 'Support-Dump/' + block.context['group'] + '/' + block.context['host']
                    for filename in block.files.keys():
                        self.write_file (path, filename, block.files[filename][0])
                    block.properties['written'] = True
            elif block.type == 'forest_status':
                # TODO better check of needed properties for path
                # Support-Dump/Default/prodrlmkg01/App-Servers/App-Services-Status.xml
                if 'group' in block.context:
                    path = 'Support-Dump/' + block.context['group'] + '/' + block.context['host'] + '/Forests/' + block.properties['database']
                    for element in block.files.keys():
                        filename = element.title() + '.xml'
                        self.write_file (path, filename, block.files[element][0])
                    block.properties['written'] = True
            elif block.type == 'triggers' and block.files:
                # TODO better check of needed properties for path
                # Support-Dump/Default/prodrlmkg01/App-Servers/App-Services-Status.xml
                if 'database' in block.properties:
                    path = 'Support-Dump/Trigger/' + block.properties['database']
                    # TODO assumption OK?
                    for file in block.files['trgr:trigger']:
                        trigger_id = self.get_xml_value ('trgr:trigger-id', file)
                        self.write_file (path, f'Trigger-{trigger_id}.xml', file)
                    block.properties['written'] = True
            elif block.type == 'xml_schemas' and block.files:
                # TODO better check of needed properties for path
                # Support-Dump/Default/prodrlmkg01/App-Servers/App-Services-Status.xml
                if 'database' in block.properties:
                    path = 'Support-Dump/Schemas/' + block.properties['database']
                    for element in block.files.keys():
                        filename = element.title() + '.xml'
                        self.write_file (path, filename, block.files[element][0])
                    block.properties['written'] = True

    def get_xml_value (self, element_name='xx-dd&&&<>', text_lines=[]):
        for line in text_lines:
            m = re.match(f'<{element_name}>(.*)</{element_name}>', line)
            if m:
                return m.group(1)
                        
                        
blocks = DumpBlocks()
line_number = 0

parser = argparse.ArgumentParser (
    description='Parse a support dump.'
)

parser.add_argument ('-file', dest='dumpfile', required=True, help='dump file to parse')
parser.add_argument ('-debug', dest='debug', default=False, help='debug output, True or False')

args = parser.parse_args()

print (args)

with open(args.dumpfile, encoding='utf-8') as dumpfile:
    for line in dumpfile:
        line_number += 1
        str = line.strip()
        blocks.add_line (str, line_number)

blocks.create_sections()
blocks.create_subsections()
blocks.reconstitute_database_topology()
blocks.remove_missing_configurations()
blocks.context_run_through()
blocks.setup_config_files()
blocks.get_check_xml_blocks()
blocks.write_files()

if args.debug:  blocks.dump()



