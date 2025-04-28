#!/usr/bin/python3

import re
import os
import sys
import string
import argparse
import copy

class DumpContext:
    def __init__(self, init_context=None):
        if init_context is None:
                self.path = []
                self.properties = []
        else:
                self.path = copy.deepcopy (init_context.path)
                self.properties = copy.deepcopy (init_context.properties)

    @staticmethod
    def copy_context (c):
        return copy.deepcopy (c)

    def find_property (self, key):
        retval = None
        for i in range (len (self.properties) - 1, -1, -1):
            if key in self.properties[i]:
                retval = self.properties[i][key]
                break
        return retval

    def get_property (self, key):
        if self.has_property (key):
            return self.properties[-1][key]
        else:
            return None

    def set_property (self, key, value):
        self.properties[-1][key] = value

    def pop_property (self, key):
        self.properties[-1].pop(key, None)

    def copy_self (self):
        return copy.deepcopy (self)

    def push_context (self, path, properties):
        self.path.append (path)
        self.properties.append (properties)

    def pop_context (self):
        self.path.pop ()
        self.properties.pop ()

    def top_properties (self):
        return self.properties[-1]

    def context_string (self):
        return repr (list (zip (self.path, self.properties)))
        #return f'{tuple (zip (self.path, self.properties))}'[0:256]

    def get_top_context (self):
        # print (f'{path} ?== {self.path[-1]}')
        return self.path[-1]

    def at_top_context (self, path):
        # print (f'{path} ?== {self.path[-1]}')
        return path == self.path[-1]

    # checks only top
    def has_property (self, key):
        # print (f'{path} ?== {self.path[-1]}')
        return key in self.properties[-1]

    def check_top_context (self, path):
        if (path != self.path[-1]):
            print (f'ERROR:  checking path {path} vs {self.path[-1]}, found mismatch.', file=sys.stderr)
        


class DumpBlock:
    def __init__(self, type='text', name='', init_context=None):
        # all start out this way
        self.type = type
        self.files = []
        self.text = []
        self.start_line = 0
        self.flags = ''
        if init_context is None:
                self.context = DumpContext()
        else:
                self.context = DumpContext.copy_context (init_context)
       
    def at_top_context (self, path):
        return self.context.at_top_context (path) 

    def add_line (self, line):
        self.text.append (line)

    def add_flag (self, flag):
        self.flags = flag

    def first_line (self):
        line = ''
        if (len (self.text) > 0):
            line = self.text[0]
        return line

    def has_lines (self):
        return len (self.text) > 0

    def dump(self, position=0, level=0):
        print ()
        print (f'>>>> {self.flags} {position}; type {self.type}; l{self.start_line}; context: ', self.context.context_string())
        if len(self.files) > 0:
                print ('>>>> ', repr (self.files))
        for line in self.text:
            print (line)

class DumpFile:

    def __init__(self, text, type):
        self.text = []
        self.type = ''

        
class DumpBlocks:

    def __init__(self):
        self.blocks = []
        self.hostname_group_mapping = {}
        self.host_id_hostname_mapping = {}

    
    def add_line (self, line, line_number):
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
            if len (self.blocks) < 1 or self.blocks[-1].type != 'text':
                if len (line) == 0:  return
                self.blocks.append (DumpBlock ('text'))
                self.blocks[-1].start_line = line_number
            
        self.blocks[-1].add_line (line)

    def block (self, block_number):
        return self.blocks[block_number]

    def len (self):
        return len (self.blocks) #self.blocks.size()

    def dump(self):
        i = 0;
        for block in self.blocks:
            block.dump(i)
            i += 1

    def get_line_key_values (self, line, properties):
        pairs = line.split (', ')
        for pair in pairs:
            key, value = pair.split (': ')
            properties[key.lower()] = value

    def config_file_subsection (self, line):
        return re.fullmatch (r'(server|groups|databases|assignments|hosts|clusters|keystore|kms|tokenizer|mimetypes)(_[0-9])?\.xml', line)

    # match the type_sequence, starting at the given block number
    def at_start_of_sequence (self, type_sequence, start_at):
        type_count = len (type_sequence)
        if type_count < 1: return False
        end_at = start_at + type_count - 1
        if end_at > len (self.blocks) - 1:  return False
        match = True
        for i in range (0, type_count - 1):
            if type_sequence[i] != self.blocks[start_at + i].type:
                    match = False
                    break
        return match

    subsection_titles = {
        'Host Status': 'host-status',
        'App Server Status': 'app-servers',
        'Database Topology': 'database-topology',
        'Forest Status': 'forest-status',
        'Trigger Definitions': 'trigger-definitions',
        'CPF Domains': 'cpf-domains',
        'CPF Pipelines': 'cpf-pipelines',
        'FlexRep Domains': 'flexrep domains',
        'SQL Schemas': 'sql schemas',
        'SQL Views': 'sql views',
        'XML Schemas': 'xml schemas',
        'Configuration': 'configuration',
        'Log Files': 'log-files',
    }

    # copies context over and sets the subtype property
    def set_next_block_subtype (self, block_number, label='heading'):
        self.block(block_number + 1).context = DumpContext.copy_context (self.block (block_number).context)
        self.block(block_number + 1).context.set_property ('subtype', label)

    def get_hostname_from_host_info (self, block):
        for line in block.text:
            print (line)
            if line.startswith ('Report Host:'):
                return re.sub (r'Report Host:\s+', '', line)
        return 'unknown-hostname-from-host-info'

    # remove notices that a file isn't there (checks for all older versions)
    def context_run_through (self):
        block_number = 0
        #context = [{'path': ['dump'], 'properties': []}]
        last_context = DumpContext ()
        last_context.push_context ('dump', {'out-dir': './Support-Dump'})
        while block_number < len (self.blocks):
            block = self.blocks[block_number]
            # carry forward the last context to start
            block.context = DumpContext.copy_context (last_context)

            # means it was considered directly in the context run through
            block.add_flag ('*')

            # dump info at start of dump
            if self.at_start_of_sequence (['bigsep', 'text', 'bigsep'], block_number) and block.context.at_top_context ('dump'):
                block.context.set_property ('host', self.get_hostname_from_host_info (self.blocks[block_number+1]))
                block.context.push_context ('dump-info', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number, 'file')
                block_number += 1
                last_context = block.context
            # dump dump-info -> dump - cluster - app-servers
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and block.context.at_top_context ('dump-info') and self.block(block_number + 1).first_line() == 'App Server Status':
                block.context.pop_context()
                # any way to get group name?  set this from the app-server level too?
                block.context.push_context('cluster', {})
                block.context.push_context('app-servers', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            # app server server-status file
            elif self.at_start_of_sequence (['subsep', 'text'], block_number) and block.context.at_top_context ('app-servers') and self.block(block_number + 1).first_line().startswith ('Group:'):
                next_block = self.block(block_number + 1)
                self.get_line_key_values (next_block.first_line(), block.context.top_properties())
                hostname = block.context.get_property('host')
                host_id = self.get_xml_value ('host-id', next_block.text)
                self.host_id_hostname_mapping[host_id] = hostname
                block.context.set_property ('host-id', host_id)
                # save mappings for the later host sections
                self.hostname_group_mapping[hostname] = block.context.get_property('group')
                self.set_next_block_subtype (block_number, 'file')
                # remove line to leave just xml
                # self.block(block_number + 1).text[0 : 1] = []
                block_number += 1
                last_context = block.context
            # Database Topology - database-dump()
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and block.context.at_top_context ('app-servers') and self.block(block_number + 1).first_line() == 'Database Topology':
                block.context.pop_context()
                # any way to get cluster name?  set this from the app-server level too?
                block.context.push_context('database-topology', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            # forest-dump
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and block.context.at_top_context ('database-topology') and self.block(block_number + 1).first_line() == 'Forest Status':
                block.context.pop_context()
                block.context.push_context('forest-status', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            # trigger-dump
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'Trigger Definitions':
                block.context.pop_context()
                block.context.push_context('trigger-definitions', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1 
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'CPF Domains':
                block.context.pop_context()
                block.context.push_context('cpf-domains', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'CPF Pipelines':
                block.context.pop_context()
                block.context.push_context('cpf-pipelines', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'FlexRep Domains':
                block.context.pop_context()
                block.context.push_context('flexrep-domains', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'SQL Schemas':
                block.context.pop_context()
                block.context.push_context('sql-schemas', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'SQL Views':
                block.context.pop_context()
                block.context.push_context('sql-views', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'XML Schemas':
                block.context.pop_context()
                block.context.push_context('xml-schemas', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'Host Status':
                block.context.push_context('host-status', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            # start of new host
            ## TODO  figure it out, what level to pop to, or restart new context?
            elif self.at_start_of_sequence (['bigsep', 'text', 'bigsep'], block_number) and self.block(block_number + 1).first_line().startswith ('Hostname:'):
                block.context.pop_context()
                block.context.pop_context()
                hostname = re.sub (r'Hostname:\s+', '', self.block(block_number + 1).first_line())
                block.context.push_context('host', {'host': hostname})
                block.context.set_property('group', self.hostname_group_mapping.get(hostname, 'UnknownGroup'))
                # mark info and skip it
                self.set_next_block_subtype (block_number, 'hostinfo')
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'Configuration':
                block.context.pop_context()
                block.context.push_context('configuration', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'Log Files':
                block.context.pop_context()
                block.context.push_context('log-files', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            elif self.at_start_of_sequence (['subsep', 'text', 'subsep'], block_number) and self.block(block_number + 1).first_line() == 'Data Directory':
                block.context.pop_context()
                block.context.push_context('data-directory', {})
                # mark heading and skip it
                self.set_next_block_subtype (block_number)
                block_number += 1
                last_context = block.context
            # set up a config file name
            elif self.at_start_of_sequence (['subsep', 'text'], block_number) and block.context.at_top_context ('configuration') and self.block(block_number + 1).first_line().endswith('.xml'):
                block.context.set_property ('filename', self.block (block_number + 1).first_line())
                block.context.pop_property ('validation-results')
                self.set_next_block_subtype (block_number, 'filename')
                block_number += 1
                last_context = block.context

            # set up a config file validation
            elif self.at_start_of_sequence (['subsep', 'text'], block_number) and block.context.at_top_context ('configuration') and self.block(block_number + 1).first_line().startswith('Validation results: '):
                block.context.set_property ('validation-results', self.block(block_number + 1).first_line()[20:])
                self.set_next_block_subtype (block_number, 'validation-results')
                block_number += 1
                last_context = block.context


            elif self.at_start_of_sequence (['subsep', 'text'], block_number) and block.context.at_top_context ('configuration') and self.block(block_number + 1).first_line().startswith('Configuration file'): # doesn't exist
                block.context.pop_property ('file')
                block.context.pop_property ('filename')
                block.context.pop_property ('validation-results')
                last_context = block.context
            # set up a log file
            elif self.at_start_of_sequence (['subsep', 'text'], block_number) and block.context.at_top_context ('log-files') and self.block(block_number + 1).first_line().endswith('.txt'):
                block.context.set_property ('filename', self.block (block_number + 1).first_line())
                self.set_next_block_subtype (block_number, 'filename')
                block_number += 1
                last_context = block.context
            # unclassified text block, must be some kind of file based on context?
            elif block.type == 'text' and 'subtype' not in block.context.properties:
                # these just get marked
                if (   block.context.at_top_context ('database-topology')
                    or block.context.at_top_context ('host-status')
                    or block.context.at_top_context ('data-directory')
                    or (block.context.at_top_context ('configuration') and not block.first_line().startswith ('Configuration file'))
                    or (block.context.at_top_context ('log-files') and block.context.has_property ('filename'))
                   ):
                    block.context.set_property ('subtype', 'file')
                # these extra db name from file text first line and remove that line
                elif (   block.context.at_top_context ('trigger-definitions')
                      or block.context.at_top_context ('cpf-domains')
                      or block.context.at_top_context ('cpf-pipelines')
                      or block.context.at_top_context ('flexrep-domains')
                      or block.context.at_top_context ('sql-schemas')
                      or block.context.at_top_context ('sql-views')
                      or block.context.at_top_context ('xml-schemas')
                    ):
                    # gotta have more than the db name
                    if len (block.text) > 1:
                            block.context.set_property ('subtype', 'file')
                            block.context.set_property ('database', block.text[0])
                    else:  block.context.set_property ('subtype', 'empty-db')
                # these extra db name from file text first line and remove that line
                elif block.context.at_top_context ('forest-status'):
                    block.context.set_property ('subtype', 'file')
                    block.context.set_property ('forest-name', block.text[0])
                    host_id = self.get_xml_value ('host-id', block.text)
                    block.context.set_property ('host-id', host_id)
                    # if this barfs KeyError ... is there a group with NO app-servers, so no mapping?  OK, default to the id
                    block.context.set_property ('hostname', self.host_id_hostname_mapping.get(host_id, host_id))
                elif block.context.at_top_context ('configuration') and block.first_line().startswith ('Configuration file'):
                    block.context.set_property ('subtype', 'missing-file')
                else:
                    block.context.set_property('subtype', 'unhandled-text')
            else:
                pass

            block_number = block_number + 1

    def get_xml_value (self, element_name='xx-dd&&&<>', text_lines=[]):
        for line in text_lines:
            m = re.match(f'<{element_name}>(.*)</{element_name}>', line)
            if m:
                return m.group(1)

    def ready_files (self):
        # go through subtype=file blocks, and save a list of the file as [filename, [start-line, end-line]] pairs
        block_number = 0
        saw_database_topology = False
        while block_number < len (self.blocks):
            block = self.blocks[block_number]
            context = block.context
            if block.type == 'text' and context.get_property ('subtype') == 'file':
                if context.at_top_context ('app-servers'):
                    path = f'{context.find_property("out-dir")}/{context.get_property("group")}/{context.get_property("host")}/App-Servers/{context.get_property("appserver")}-Status.xml'
                    block.files.append ([path, [1, len(block.text) - 1]])
                elif context.at_top_context ('dump-info'):
                    path = f'{context.find_property("out-dir")}/Support-Request.txt'
                    block.files.append ([path, [1, len(block.text) - 1]])
                elif context.at_top_context ('database-topology'):
                    block.context.set_property ('header', '===================================')
                    path = f'{context.find_property("out-dir")}/Database-Topology.txt'
                    block.files.append ([path, [0, len(block.text) - 1]])
                    if saw_database_topology == False:
                        saw_database_topology = True
                    else: 
                        block.context.set_property ('write-mode', 'append')
                elif context.at_top_context ('configuration'):
                    path = f'{context.find_property("out-dir")}/{context.find_property("group")}/{context.find_property("host")}/Configuration/{context.get_property("filename")}'
                    block.files.append ([path, [0, len(block.text) - 1]])
                elif context.at_top_context ('log-files'):
                    filename = re.sub (r'.*/', '', context.get_property ('filename'))
                    path = f'{context.find_property("out-dir")}/{context.find_property("group")}/{context.find_property("host")}/Logs/{filename}'
                    block.files.append ([path, [0, len(block.text) - 1]])
                elif context.at_top_context ('host-status'):
                    self.get_check_xml (block)
                elif context.at_top_context ('forest-status'):
                    self.get_check_xml (block)
                elif context.at_top_context ('cpf-domains'):
                    self.get_check_xml (block)
                elif context.at_top_context ('xml-schemas'):
                    self.get_check_xml (block)
                elif context.at_top_context ('sql-views'):
                    self.get_check_xml (block)
                elif context.at_top_context ('sql-schemas'):
                    self.get_check_xml (block)
                elif context.at_top_context ('trigger-definitions'):
                    self.get_check_xml (block)
                elif context.at_top_context ('cpf-pipelines'):
                    self.get_check_xml (block)
                #elif context.at_top_context ('flexrep-domains'):
                else:
                    block.context.set_property ('unhandled', 'true')
            block_number = block_number + 1
        
    def get_check_xml (self, block):
        lines = block.text
        context = block.context
        current_element = '---';
        line_number = 0
        start_line = -1
        file_number = 1
        for line in lines:
            #print (f'block l{block.start_line}, line {line_number}')
            # sometimes first line is not part of the file
            if context.get_top_context() in ['xml-schemas','sql-schemas','trigger-definitions','forest-status','cpf-domains','cpf-pipelines'] and line_number == 0:
                line_number += 1
                continue
            m = re.match(r'\s*<(/?)([^>\s]+)', line)
            if m:
                end_slash, element_name = m.group(1), m.group(2)
                #print ('   match ' + end_slash + element_name)
                if end_slash:
                    # end element
                    if current_element == element_name:
                        end_line = line_number
                        # nice, matched up
                        #print ('< obai ' + element_name)
                        #trigger_id = self.get_xml_value ('trgr:trigger-id', block.text)
                        # get filename
                        filename = element_name
                        if context.at_top_context ('xml-schemas'):
                            path = f'{context.find_property("out-dir")}/Schemas/{context.get_property("database")}/Schema-{file_number}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('trigger-definitions'):
                            trigger_id = self.get_xml_value ('trgr:trigger-id', block.text[start_line:end_line])
                            path = f'{context.find_property("out-dir")}/Triggers/{context.get_property("database")}/Trigger-{trigger_id}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('sql-schemas'):
                            schema_id = self.get_xml_value ('view:schema-id', block.text)
                            path = f'{context.find_property("out-dir")}/SQL/{context.get_property("database")}/Schema-{schema_id}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('sql-views'):
                            view_id = self.get_xml_value ('view:view-id', block.text)
                            path = f'{context.find_property("out-dir")}/SQL/{context.get_property("database")}/View-{view_id}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('cpf-pipelines'):
                            id = self.get_xml_value ('p:pipeline-id', block.text)
                            path = f'{context.find_property("out-dir")}/CPF/{context.get_property("database")}/Pipeline-{id}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('cpf-domains'):
                            if element_name == 'dom:domain':
                                domain_id = self.get_xml_value ('dom:domain-id', block.text[start_line : end_line])
                                path = f'{context.find_property("out-dir")}/CPF/{context.get_property("database")}/Domain-{domain_id}.xml'
                            elif element_name == 'dom:configuration':
                                configuration_id = self.get_xml_value ('dom:config-id', block.text[start_line : end_line])
                                path = f'{context.find_property("out-dir")}/CPF/{context.get_property("database")}/Configuration-{configuration_id}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('forest-status'):
                            hostname = block.context.find_property("hostname")
                            group = self.hostname_group_mapping.get(hostname, 'UnknownGroup')
                            #path = f'{context.find_property("out-dir")}/{group}/{hostname}/Forests/{forest_name}/Forest-Status.xml'
                            filename = element_name.title()
                            path = f'{context.find_property("out-dir")}/{group}/{hostname}/Forests/{block.context.find_property("forest-name")}/{filename}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        elif context.at_top_context ('host-status'):
                            hostname = block.context.find_property("host")
                            group = self.hostname_group_mapping.get(hostname, 'UnknownGroup')
                            filename = element_name.title()
                            path = f'{context.find_property("out-dir")}/{group}/{hostname}/{filename}.xml'
                            block.files.append ([path, [start_line, end_line]])
                        current_element = '---';
                        start_line = -1
                        file_number += 1
                else:
                    # start element
                    if current_element == '---':
                        #print ('> ohai ' + element_name)
                        start_line = line_number
                        current_element = element_name
            elif start_line == -1:
                print ('ERROR: unowned line at about line ', block.start_line + line_number)

            line_number += 1


    def write_files (self):
        for block in self.blocks:
            for file in block.files:
                path, limits = file

                m = re.match(r'^(.*)/(.*)', path)
                dirs, filename = m.group(1), m.group(2)

                os.makedirs (dirs, 0o777, True)
                write_mode = 'a' if block.context.get_property ('write-mode') == 'append' else 'w' 
                with open(path, write_mode) as f:
                    if block.context.get_property ('header'):
                        f.write (block.context.get_property ('header') + '\n')
                    for line in block.text[limits[0]:limits[1] + 1]:
                        f.write (line + '\n')



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

#if args.debug:  blocks.dump()


# where do I do this?

#        # get rid of leading blank lines in text blocks
#        if block.type == 'text':
#            while block.has_lines() and re.fullmatch (r'\s*', block.text[0]):
#                block.text[0:1] = []



blocks.context_run_through()
blocks.ready_files()
blocks.write_files()

if args.debug:  blocks.dump()

# blocks.write_files()




