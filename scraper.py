from os import listdir, makedirs
from os.path import isfile, join, exists
import mistune
from bs4 import BeautifulSoup
import re
import json

SECTIONS = []
PATH = './okta.github.io/_source/_docs/api/resources/'
markdown_files = [f for f in listdir(PATH) if isfile(join(PATH, f))]

def get_endpoint(soup):
    start = soup.find('{% api_operation') + 17
    end = soup.find(' %}')
    span = soup[start:end].split(' ')
    if len(span) > 0:
        return span
    return

def get_summary(blob):
    lines = blob.split("\n")
    if len(lines) > 0:
        return lines[0].replace("### ", "")
    return

def get_description_location(lines):
    # Returns the index of the span object
    index = 0
    for line in lines:
        index += 1
        if '{% api_operation' in line:
            #<span
            return index

def get_description(blob):
    lines = blob.strip().split("\n")

    #Reformat object to remove newlines
    lines = [l for l in lines if l]
    location = get_description_location(lines)
    try:
        return lines[location]
    except IndexError:
        return ""

def get_misc_text(blob):
    lines = blob.strip().split("\n")
    lines = [l for l in lines if l]

    location = get_description_location(lines) + 1
    if location:
        return '\n'.join([str(x) for x in lines[location:]])

def find_body(tag):
    if '{:' in tag.text:
        return tag.findNext('p')
    else:
        return tag

def find_examples(md_file):
    # Rewind file
    md_file.seek(0)
    found_examples = []
    found_params = []

    mkdown = mistune.markdown(md_file.read())

    soup = BeautifulSoup(mkdown, 'html.parser')

    # Find main example headers
    headers = soup.find_all('h4')

    for header in headers:
        if 'ObjectClass:' not in header.text and 'Example' not in header.text and 'Parameters' not in header.text:
            description = find_body(header.findNext('p'))
            request = description.findNext('pre')

            # Format return objects
            if description:
                description = description.text

            if request:
                request = request.text

            found_examples.append({'key': header.text, 'description': description, 'curl': request})

    # Find main example headers
    req_headers = soup.find_all('h5')
    for header in req_headers:
        if 'Request Parameters' in header.text:
            key = header.findPrevious('h3')
            table = header.findNext('table')

            rows = table.find_all('tr')
            row_headers = rows[0]
            parsing_rows = rows[1:]

            params = []
            index = 0
            for row in parsing_rows:
                parameters = {}
                vals = row.text.split('\n')
                vals = [v for v in vals if v]
                parameters['name'] = vals[0]
                parameters['description'] = vals[1]
                params.append(parameters)

            found_params.append({'summary': key.text, 'parameters': params})            

    return found_examples, found_params

def find_sections(md_file):
    found_sections = []
    component = ""
    running = False

    for line in md_file:

        if re.match('### ', line):
            running = True
            if '{% api_operation' in component:
                #'<span ' in component or 
                found_sections.append(component)
            component = line

        else:
            if running:
                if re.match('#### ', line) or re.match('##### ', line):
                    running = False
                else:
                    component += line + "\n"

    return found_sections

def find_tags(md_file):
    md_file.seek(0)
    found_tags = []

    mkdown = mistune.markdown(md_file.read())
    soup = BeautifulSoup(mkdown, 'html.parser')

    # Find main example headers
    headers = soup.find_all('h3')
    for header in headers:
        try:
            blockquote = header.findNext('blockquote').findNext('p')
            if 'api_lifecycle' in blockquote.text:
                tag = blockquote.text
                tag = tag.split('api_lifecycle')
                found_tags.append({'key': header.text, 'tag': tag[1].split('%')[0]})
        except Exception as e:
            continue
    return found_tags

def create_dirs(directories_given):
    for name in directories_given:
        if not exists(name) and name != '':
            makedirs(name)
    
def create_file(path, name, type, text):
    if not exists(path):
        raise ValueError("Invalid path")

    new_file_path = "{}/{}.{}".format(path, name, type)
    with open(new_file_path, "w") as f:
        f.write(text)

def get_keys(blob):
    keys = []
    lines = blob.split('\n')
    for line in lines:
        if '#' in line:
            keys.append(line.split('#')[1][:-1].replace('-', ' '))
    return keys

def curl_to_json(method, curl):
    headers = {}

    if 'curl' not in curl:
        # Only want curl requests
        return None

    for line in curl.split('\n'):
        if '-H' in line:
            line = line.split('"')[1]
            header = line.split(":")
            headers[header[0]] = header[1]
    
    # Get json request body
    json_params = None
    url = None

    json_parse = curl.split('curl')[1]

    if '-d' in json_parse:
        # If body params
        json_parse = json_parse.split('-d')[1].strip()
        split_json = json_parse.split("https://")
        url = "https://{}".format(split_json[-1])[:-1]

        # Remove whitespace and single quotes
        json_params = split_json[0][1:-3]

    else:
        url = "https://{}".format(json_parse.split("https://")[-1])

    request = {
        'method': str(method),
        'headers': headers,
        'json': json_params,
        'url': url
    }
    return request

def parse_examples(blob, examples, method):
    keys = get_keys(blob)
    example_list = []
    for example in examples:
        if example['key'].lower() in keys:
            request = curl_to_json(method, example['curl'].strip())
            example_list.append(
                {'key': example['key'], 'description': example['description'], 'request': request}
            )

    return example_list

def get_dicts(f):
    api = []

    with open(PATH + f, 'r') as md_file:
        
        # Break markdown file into sections and examples
        sections = find_sections(md_file)
        examples, params = find_examples(md_file)
        tags = find_tags(md_file)

        # Parse these sections
        for section in sections:
            soup = BeautifulSoup(section, 'html.parser')
            #endpoint = get_endpoint(soup)
            endpoint = get_endpoint(section)
            summary = get_summary(section)
            description = get_description(section)
            misc = get_misc_text(section)
            
            # Save to object
            if endpoint and len(endpoint) > 0:
                filename = endpoint[1][1:].replace('/', '-').replace('*:', '').replace('*', '').split('?')[0]
                # Create directories for markdown files
                directories = [filename, "{}/{}".format(filename, endpoint[0].upper())]
                
                create_dirs(directories)

                file_path = filename + "/" + endpoint[0]

                # Create description markdown file
                create_file(file_path, "description", "md", description)

                # Create schema data json file
                for param in params:
                    if param['summary'] == summary:
                        tag = [t for t in tags if t['key'] == summary]
                        if tag:
                            param['release_cycle'] = tag[0]['tag'].upper().strip()
                        create_file(file_path, "schema", "json", json.dumps(param, indent=2, sort_keys=True))

                if misc:
                    markdown_examples = parse_examples(misc, examples, endpoint[0])
                    for example in markdown_examples:
                        folder_path = "{}/{}/{}/{}".format(filename, endpoint[0], "examples", example['key'].replace(' ', '-'))
                        create_dirs([folder_path])
                        create_file(folder_path, "description", "md", example['description'])
                        create_file(folder_path, "example", "json", json.dumps(example['request'], indent=2, sort_keys=True))               

    return api

def delete_old_folders():
    import os, shutil
    folders = [name for name in os.listdir('./')
            if os.path.isdir(os.path.join('./', name)) and name != 'okta.github.io']
    for folder in folders:
        shutil.rmtree(folder)

def walkthrough():
    # Walk through all documented md files
    delete_old_folders()
    for f in markdown_files:    
        print("Parsing [ {} ]".format(f))
        api = get_dicts(f)
            

if __name__ in "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == 'clean':
            # Delete all existing folders
            delete_old_folders()
        else:
            walkthrough()
    else:
        walkthrough()
