import copy
import os
import re
import string
import xml.etree.ElementTree as ET
from tkinter import *
from tkinter import messagebox, simpledialog
from tkinter.filedialog import askopenfilename
import tkinter as tk

import pycountry


def sup_sub_decode(html):
    """Decodes superscript and subscript tags"""
    decoded_html = html.replace('s#p', '<sup>').replace('p#s', '</sup>').replace('s#b', '<sub>').replace('b#s',
                                                                                                         '</sub>')
    return decoded_html


class QcTool:

    def __init__(self, xml_file_name):
        self.file_name = xml_file_name

    def remove_duplicate_authors(self):
        tree = ET.parse(f'{self.file_name}.xml')
        xml_doc = tree.getroot()
        required_indexes = []
        for article in xml_doc.findall('Presentation'):
            manual_id = article.find('ManualId').text
            authors = article.find('Authors').findall('Author')
            visited_authors = []
            author_unwanted_indexes = []
            for n_author, author in enumerate(authors):
                merged_authors = ''
                if author.find('FirstName').text is not None:
                    first_name = author.find('FirstName').text.strip().lower()
                    merged_authors += first_name
                if author.find('LastName').text is not None:
                    last_name = author.find('LastName').text.strip().lower()
                    merged_authors += last_name
                if author.find('Suffix') is not None:
                    suffix = author.find('Suffix').text.strip().lower()
                    merged_authors += suffix
                if merged_authors not in visited_authors:
                    visited_authors.append(merged_authors)
                else:
                    author_unwanted_indexes.append(n_author)
                    required_index = visited_authors.index(merged_authors)
                    print(manual_id, n_author + 1)
                    if author.find('AffiliationLinks').find('AffiliationLink') is None:
                        continue
                    try:
                        to_remove_author_sequences = [sequ.attrib['AffiliationSeq'] for sequ in
                                                      author.find('AffiliationLinks').findall('AffiliationLink')]
                    except:
                        continue
                    required_author = article.find(f'Authors//Author[@AuthorSeq="{required_index + 1}"]')
                    link_required = required_author.find('AffiliationLinks')
                    for number in to_remove_author_sequences:
                        inner_link = ET.Element('AffiliationLink')
                        inner_link.attrib['AffiliationSeq'] = f"{number}"
                        link_required.append(inner_link)
            to_remove_authors = article.find('Authors')
            for n, remove_index in enumerate(author_unwanted_indexes):
                to_remove_authors.remove(to_remove_authors[remove_index - n])
            authors = article.find('Authors').findall('Author')
            for author in authors:
                unwanted_seq = []
                visited_seq = []
                for n, link in enumerate(author.find('AffiliationLinks')):
                    try:
                        seq_link = link.attrib['AffiliationSeq']
                        if seq_link not in visited_seq:
                            visited_seq.append(seq_link)
                        else:
                            unwanted_seq.append(n)
                    except:
                        continue

                links = author.find('AffiliationLinks')
                print(len(links.findall('AffiliationLink')))
                print(unwanted_seq)
                for n_link, link in enumerate(unwanted_seq):
                    links.remove(links[link - n_link])

            for n_author, author in enumerate(authors, start=1):
                author.attrib['AuthorSeq'] = f"{n_author}"

        for n, remove_index in enumerate(required_indexes):
            xml_doc.remove(xml_doc[remove_index - n])
        tree.write(f'{self.file_name}_v1.xml', xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Duplicate Authors Removed Successfully..!")
        raise SystemExit

    def find_box_value(self):
        if os.path.exists(f'{self.file_name}_Box_Values.txt'):
            os.remove(f'{self.file_name}_Box_Values.txt')
        master_list = []
        master_list.extend(list(string.ascii_letters))
        master_list.extend(list(string.ascii_uppercase))
        master_list.extend(list(string.punctuation))
        master_list.extend(list(string.digits))
        master_list.extend(list(string.whitespace))

        tree = ET.parse(f'{self.file_name}.xml')
        xml_doc = tree.getroot()
        for article in xml_doc.findall('Presentation'):
            manual_id = article.find('ManualId').text
            print(manual_id)
            cleaned_tag = ET.tostring(article, encoding='unicode')
            count_of_box_values = 0
            letters = ''
            for letter in cleaned_tag:
                if letter not in master_list:
                    count_of_box_values += 1
                    letters += letter
            if count_of_box_values:
                self.write_box_value(self.file_name, f'{count_of_box_values} found in {manual_id} --- {letters}')
        messagebox.showinfo("Tool Validation", "Box Values Found Successfully..!")
        raise SystemExit

    def unwanted_title_remover(self):
        txt_file_name = askopenfilename()

        with open(txt_file_name, 'r', encoding='utf-8') as file:
            text = file.read().replace('<Title Language="eng">', '').replace('</Title>', '')
        unwanted_title = text.split('\n')
        while '' in unwanted_title:
            unwanted_title.remove('')
        print('Removing Unwanted Titles From Xml ----> ', self.file_name)
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        seq = 1
        removable_indexes = []
        for article in xml_doc.findall('Presentation'):
            print(article.find('ManualId').text.strip())
            article_title = self.strip_it(
                ET.tostring(article.find('Titles//Title'), encoding='unicode').replace('<Title Language="eng">',
                                                                                       '').replace('</Title>',
                                                                                                   '').strip())
            if article_title in unwanted_title:
                removable_indexes.append(seq - 1)
            seq += 1

        for removed_item, index in enumerate(removable_indexes, start=0):
            xml_doc.remove(xml_doc[index - removed_item])

        tree.write(f"{self.file_name}_v1.xml", xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Unwanted Titles Removed Successfully..!")
        raise SystemExit

    def unwanted_org_remover(self):
        txt_file_name = askopenfilename()
        with open(txt_file_name, 'r', encoding='utf-8') as file:
            text = file.read().replace('<Organisation>', '').replace('</Organisation>', '')
        unwanted_org = text.split('\n')
        while '' in unwanted_org:
            unwanted_org.remove('')
        print('Removing Unwanted Organization From Xml ----> ', self.file_name)
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        seq = 1
        for article in xml_doc.findall('Presentation'):
            print(article.find('ManualId').text.strip())
            seq += 1
            removable_indexes = []
            for n, affiliation in enumerate(article.find('Affiliations').findall('Affiliation')):
                if affiliation.find('Organisation').text.strip() in unwanted_org:
                    removable_indexes.append(n)
            affiliations = article.find('Affiliations')
            for n, remove_index in enumerate(removable_indexes):
                affiliations.remove(affiliations[remove_index - n])
            available_sequences = []
            for affiliation in affiliations.findall('Affiliation'):
                available_sequences.append(affiliation.attrib['AffiliationSeq'])

            for author in article.find('Authors').findall('Author'):
                for link in author.find('AffiliationLinks').findall('AffiliationLink'):
                    try:
                        if link.attrib['AffiliationSeq'] not in available_sequences:
                            link.clear()
                    except:
                        continue

            old_new_data_dict = {}
            aff_seq = 1
            for aff in article.find('Affiliations').findall('Affiliation'):
                old_seq = aff.attrib['AffiliationSeq']
                old_new_data_dict[old_seq] = aff_seq
                aff.attrib['AffiliationSeq'] = f"{aff_seq}"
                aff_seq += 1
            for author in article.find('Authors').findall('Author'):
                for link in author.find('AffiliationLinks').findall('AffiliationLink'):
                    try:
                        existing_seq = link.attrib['AffiliationSeq']
                    except:
                        continue
                    updated_seq = old_new_data_dict[existing_seq]
                    link.attrib['AffiliationSeq'] = f"{updated_seq}"

        tree.write(f"{self.file_name}_v1.xml", xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Unwanted Organizations Removed Successfully..!")
        raise SystemExit

    def remove_new_lines(self):
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        for abstract in xml_doc.iter('Abstract'):
            abstract_text = ET.tostring(abstract, encoding='unicode').replace('<Abstract Language="eng">', '').replace(
                '</Abstract>', '')
            abstract_text = self.strip_it(abstract_text).strip()
            abstract.clear()
            abstract.attrib['Language'] = 'eng'
            abstract.text = abstract_text
        for abstract in xml_doc.iter('Title'):
            abstract_text = ET.tostring(abstract, encoding='unicode').replace('<Title Language="eng">', '').replace(
                '</Title>', '')
            abstract_text = self.strip_it(abstract_text).strip()
            abstract.clear()
            abstract.attrib['Language'] = 'eng'
            abstract.text = abstract_text
        data = ET.tostring(xml_doc, encoding='unicode', xml_declaration=True)
        data = data.replace('</Abstract><PresentationUrl>', '</Abstract>\n<PresentationUrl>')
        data = data.replace('</Title></Titles>', '</Title>\n</Titles>')
        data = data.replace('&lt;img', '<img').replace('&lt;sup&gt;', '<sup>') \
            .replace('&lt;/sup&gt;', '</sup>').replace('.jpg" /&gt;', '.jpg" />') \
            .replace('.gif" /&gt;', '.gif" />').replace('.png" /&gt;', '.png" />') \
            .replace('.JPG" /&gt;', '.JPG" />').replace('.GIF" /&gt;', '.GIF" />') \
            .replace('.jpeg" /&gt;', '.jpeg" />').replace('.PNG" /&gt;', '.PNG" />') \
            .replace('.JPEG" /&gt;', '.JPEG" />').replace('.tif" /&gt;', '.tif" />') \
            .replace('.jfif" /&gt;', '.jfif" />').replace('.pjpeg" /&gt;', '.pjpeg" />') \
            .replace('.pjp" /&gt;', '.pjp" />').replace('&lt;/ sub&gt;', ' </sub>') \
            .replace("encoding='cp1252'", "encoding='UTF-8'")
        data = data.replace('&lt;sub&gt;', '<sub>').replace('&lt;/sub&gt;', '</sub>').replace('', '"') \
            .replace('', '"').replace('', "'").replace('', "'").replace('', '-') \
            .replace('ã', '').replace('ã', '').replace('ï¼', '<').replace('â§', '≧') \
            .replace('â', '"').replace('â', '"').replace('ï¼', ')').replace('ï¼', '(') \
            .replace('â£', 'IV').replace('â¢', 'III').replace('ï¼', '+').replace('ï¼', '>') \
            .replace('ï¼', ':').replace('ï¼', '.').replace('â¡', 'II').replace('â¢', 'III') \
            .replace('â', "’").replace('', '•').replace('', '—').replace('', '⋯') \
            .replace('', '').replace('ï¬', 'fi').replace("â'", '−').replace('â"', '–') \
            .replace('', '™').replace('‐', '-').replace('Ⓡ', '®').replace(' ', '').replace('‐', '-') \
            .replace('Ⅱ', 'II').replace('Ⅲ', 'III').replace('&lt; /sub&gt;', '</sub>') \
            .replace('&lt;/ sub&gt;', '</sub>').replace('&lt;sub &gt;', '<sub>').replace('&lt; sup&gt;', '<sup>') \
            .replace('&lt; sup&gt;', '<sup>').replace('&lt;sup &gt;', '<sup>').replace('&lt; /sub&gt;', '</sub>') \
            .replace('&lt;/ sub&gt;', '</sub>').replace('&lt;/sub &gt;', '</sub>').replace('&lt; /sup&gt;', '</sup>') \
            .replace('&lt;/ sup&gt;', '</sup>').replace('&lt;/sup &gt;', '</sup>').replace('α', 'α').replace('ß', 'ss') \
            .replace('Ⅳ', 'IV').replace('Ⅳ', 'IV').replace('𝛽', 'β').replace('𝛃', 'β').replace('𝛾', 'γ') \
            .replace('γ', 'γ').replace('𝜀', 'ε').replace('ﬁ', 'fi').replace('，', ',').replace('＝', '=') \
            .replace('⁄', '/').replace('&lt; sub&gt;', '<sub> ').replace('¹', '<sup>1</sup>') \
            .replace('²', '<sup>2</sup>').replace('³', '<sup>3</sup>').replace('⁴', '<sup>4</sup>') \
            .replace('⁵', '<sup>5</sup>').replace('⁶', '<sup>6</sup>').replace('⁸', '<sup>8</sup>').replace('',
                                                                                                            'ff').replace(
            '', 'ff') \
            .replace('', 'fi').replace('', 'β').replace('Ã', 'Á').replace('', ',').replace('', '5') \
            .replace('', "'").replace('', '').replace('', '').replace('', '').replace('', '')
        data = sup_sub_decode(data)
        with open(f'{self.file_name}_v1.xml', 'w', encoding='utf-8') as file:
            file.write(data)
        messagebox.showinfo("Tool Validation", "New Lines Removed Successfully..!")
        raise SystemExit

    def remove_repeated_organization(self):
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        """Iterating Over the presentations"""
        for presentation in xml_doc.findall('Presentation'):
            affiliations = presentation.find('Affiliations')
            already_there_affiliations = []  # For Duplicate Organisation storing
            affiliation_indexes = []  # Storing the indexes of the duplicates to remove it later
            ciruculating_index = 0  # To track the affiliation which is duplicate
            new_seq_num = 1  # To use it as an key for the dictionary ad value as removed affiliation seq
            new_to_old = {}  # Dictionary for {key(new_seq_num) : value(old_seq_numbers)}

            """Iterating Over the Affiliations"""
            for affiliation in affiliations:
                organisation_name = affiliation.find('Organisation').text
                old_seq_num = affiliation.attrib['AffiliationSeq']
                if organisation_name.strip() not in already_there_affiliations:
                    already_there_affiliations.append(organisation_name.strip())
                    new_to_old[new_seq_num] = [old_seq_num]
                    new_seq_num += 1  # Increments if the organisation is new to add another key to the dict
                else:
                    affiliation_indexes.append(
                        ciruculating_index)  # Appends the index only if it exists in the already..list to remove it later
                    index_num_old = already_there_affiliations.index(organisation_name.strip()) + 1
                    new_to_old[index_num_old].append(
                        old_seq_num)  # Appending the old value to the above repeated stored key in new_to_old dict
                ciruculating_index += 1

            """Removing the duplicates from the list of affiliations using the index"""
            for removed_item, index in enumerate(affiliation_indexes, start=0):
                affiliations.remove(affiliations[index - removed_item])

            """Removing the affiliation unordered seq to allocate the new one"""
            for n, affiliation in enumerate(affiliations, start=1):
                affiliation.set('AffiliationSeq', str(n))

            """Iterating the affiliation link seq in the author to replace it with the key of new_to_old"""
            for affiliation_link in presentation.iter('AffiliationLink'):
                author_linked_seq = affiliation_link.attrib['AffiliationSeq']
                for key, value in new_to_old.items():
                    if author_linked_seq in value:
                        affiliation_link.set('AffiliationSeq', str(key))
        tree.write(f'{self.file_name}_v1.xml', encoding='UTF-8', xml_declaration=True)
        messagebox.showinfo("Tool Validation", "Repeated Organizations Removed Successfully..!")
        raise SystemExit

    def align_organizations(self):
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        """Iterating Over the presentations"""
        all_organizations = []
        for presentation in xml_doc.iter('Organisation'):
            if presentation.text not in all_organizations:
                all_organizations.append(presentation.text)
        all_organizations.sort(key=len)
        for org in all_organizations:
            with open(f'A-Z_Organization_{self.file_name.split("/")[-1]}.txt', 'a', encoding='utf-8') as file:
                file.write(f"<Organisation>{org}</Organisation>\n")
        messagebox.showinfo("Tool Validation", "Organizations Written in a file Successfully..!")
        raise SystemExit

    def get_country_by_code(self, country):
        if len(country) == 2:
            return pycountry.countries.get(alpha_2=country).name
        elif len(country) == 3:
            return pycountry.countries.get(alpha_3=country).name

    def country_code_splitter(self):
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        for og in xml_doc.iter('Organisation'):
            try:
                code = og.text.split(',')[-1].strip()
                country = self.get_country_by_code(code)
                og.text = og.text.replace(code, country)
            except:
                pass

        tree.write(f"{self.file_name}_v1.xml", xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Country Codes Elaborated Successfully..!")
        raise SystemExit

    def semicolon_splitter(self):
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        for article in xml_doc.findall('Presentation'):
            manual_id = article.find('ManualId').text
            print(manual_id)
            affiliations = article.find('Affiliations').findall('Affiliation')
            data_dict = {}
            for n, affiliation in enumerate(affiliations):
                org_text = affiliation.find('Organisation').text
                affiliation.find('Organisation').text = org_text.split(';')[0]
                value_to_start = n + 1
                if ';' in org_text:
                    for org in org_text.split(';'):
                        org_copy = copy.deepcopy(affiliation)
                        org_copy.find('Organisation').text = org
                        org_copy.attrib['AffiliationSeq'] = '0'
                        data_dict[value_to_start] = org_copy
                        value_to_start += 1

            affiliations = article.find('Affiliations')
            for key, value in data_dict.items():
                affiliations.insert(key, data_dict[key])

        for article in xml_doc.findall('Presentation'):
            authors = article.find('Authors').findall('Author')
            manual_id = article.find('ManualId').text
            print(manual_id)

            author_data_dict = {}
            for author in authors:
                no_of_author_seq = author.attrib['AuthorSeq']
                author_data_dict[no_of_author_seq] = []
                for link in author.find('AffiliationLinks').findall('AffiliationLink'):
                    link_sequence = int(link.attrib['AffiliationSeq'])
                    try:
                        author_data_dict[no_of_author_seq].append(link_sequence)
                    except:
                        author_data_dict[no_of_author_seq] = [link_sequence]
            affiliations = article.find('Affiliations').findall('Affiliation')
            affiliation_data_dict = {}
            last_key = 1
            affiliation_data_dict[last_key] = [1]
            for n, affiliation in enumerate(affiliations, start=1):
                existing_seq = int(affiliation.attrib['AffiliationSeq'])
                if existing_seq != 0:
                    last_key = existing_seq
                    try:
                        affiliation_data_dict[existing_seq].append(n)
                    except:
                        affiliation_data_dict[existing_seq] = [n]
                else:
                    if n not in affiliation_data_dict[last_key]:
                        affiliation_data_dict[last_key].append(n)
            authors = article.find('Authors').findall('Author')
            for author in authors:
                no_of_author_seq = author.attrib['AuthorSeq']
                length_of_links = len(author.find('AffiliationLinks').findall('AffiliationLink'))
                for i in range(length_of_links):
                    author.find('AffiliationLinks').remove(author.find('AffiliationLinks')[0])
                try:
                    for values in author_data_dict[no_of_author_seq]:
                        for affiliation_key in list(set(affiliation_data_dict[values])):
                            ET.SubElement(author.find('AffiliationLinks'), 'AffiliationLink',
                                          AffiliationSeq=f'{affiliation_key}')
                except Exception as e:
                    print(e)
                    print(article.find('ManualId').text)

            affiliations = article.find('Affiliations').findall('Affiliation')
            for n, affiliation in enumerate(affiliations, start=1):
                affiliation.attrib['AffiliationSeq'] = str(n)

        tree.write(f"{self.file_name}_v1.xml", xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Semicolon Separated Organization Splitted  Successfully..!")
        raise SystemExit

    def unwanted_image_link_removal(self):
        txt_file_name = askopenfilename()
        with open(txt_file_name, 'r', encoding='utf-8') as file:
            text = file.read().replace('<Organisation>', '').replace('</Organisation>', '').strip()
        unwanted_image_links = text.split('\n')
        while '' in unwanted_image_links:
            unwanted_image_links.remove('')
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        for article in xml_doc.iter('img'):
            if article.attrib['src'].split('/')[-1] in unwanted_image_links:
                article.clear()

        tree.write(f"{self.file_name}_v1.xml", xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Unwanted Image Links Removed Successfully..!")
        raise SystemExit

    def change_datas(self):
        field_label = simpledialog.askstring("User Input", "Enter Field For Comparison:")
        field_to_change = simpledialog.askstring("User Input", "Which Field To Change ?")
        field_data_dict = {
            'PresentationType': 0,
            'AbstractNumber': 2,
            'Titles': 3,
            'Authors': 4,
            'Affiliations': 5,
            'Abstract': 6,
            'PresentationUrl': 7,
            'doiID': 8,

        }

        if not field_label:
            field_label = 'PresentationUrl'
        tree = ET.parse(f"{self.file_name}.xml")
        xml_doc = tree.getroot()
        required_indexes = {}
        for article in xml_doc.findall('Presentation'):
            manual_id = ET.tostring(article.find(field_label), encoding='unicode')
            required_indexes[manual_id] = article.find(field_to_change)

        destination_file_name = askopenfilename()

        tree = ET.parse(destination_file_name)
        xml_doc = tree.getroot()
        seq = 0
        for article in xml_doc.findall('Presentation'):
            manual_id = ET.tostring(article.find(field_label), encoding='unicode')
            if manual_id in required_indexes:
                article.remove(article.find(field_to_change))
                abstract = required_indexes[manual_id]
                index_of_data = field_data_dict[field_to_change]
                article.insert(index_of_data, abstract)

        destination_file_name_v1 = destination_file_name.replace('.xml', '_v1.xml')

        tree.write(destination_file_name_v1, xml_declaration=True, encoding='UTF-8')
        messagebox.showinfo("Tool Validation", "Datas Changed Successfully..!")
        raise SystemExit

    @staticmethod
    def write_box_value(xml_file_name, text):
        with open(f'{xml_file_name}_Box_Values.txt', 'a', encoding='utf-8') as file:
            file.write(f'{text}\n')

    @staticmethod
    def strip_it(text):
        return re.sub('\s+', ' ', text)

    @staticmethod
    def prettify(element, indent=''):
        queue = [(0, element)]  # (level, element)
        while queue:
            level, element = queue.pop(0)
            children = [(level + 1, child) for child in list(element)]
            if children:
                element.text = '\n' + indent * (level + 1)  # for child open
            if queue:
                element.tail = '\n' + indent * queue[0][0]  # for sibling open
            else:
                element.tail = '\n' + indent * (level - 1)  # for parent close
            queue[0:0] = children  # prepend so children come before siblings


def take_input(inputtxt, root):
    inp = inputtxt.get(1.0, "end-1c")
    file_name = askopenfilename().replace('.xml', '')
    print(file_name)
    tool_obj = QcTool(file_name)
    if int(inp) == 1:
        tool_obj.find_box_value()
    elif int(inp) == 2:
        tool_obj.remove_duplicate_authors()
    elif int(inp) == 3:
        tool_obj.unwanted_title_remover()
    elif int(inp) == 4:
        tool_obj.unwanted_org_remover()
    elif int(inp) == 5:
        tool_obj.remove_new_lines()
    elif int(inp) == 6:
        tool_obj.remove_repeated_organization()
    elif int(inp) == 7:
        tool_obj.align_organizations()
    elif int(inp) == 8:
        tool_obj.country_code_splitter()
    elif int(inp) == 9:
        tool_obj.semicolon_splitter()
    elif int(inp) == 10:
        tool_obj.unwanted_image_link_removal()
    elif int(inp) == 11:
        tool_obj.change_datas()
    # func_dict = {
    #     1: tool_obj.find_box_value(),
    #     2: tool_obj.remove_duplicate_authors(),
    #     3: tool_obj.unwanted_title_remover(),
    #     4: tool_obj.unwanted_org_remover(),
    #     5: tool_obj.remove_duplicate_authors()
    # }

    w = Label(root, text='Tool', font="50")
    w.pack()


if __name__ == '__main__':
    root = tk.Tk()
    root.title("QC All-In-One Tool")

    # Create the label
    l = tk.Label(root, text="""Select an option from the list below:\n
    (1) Box value\n
    (2) Duplicate author remove\n
    (3) Unwanted Title Tool\n
    (4) Organisation Remove tool\n
    (5) New line remove tool\n
    (6) Remove Repeated Affiliations\n
    (7) A-Z Organizations\n
    (8) Elaborate Country\n
    (9) Semicolon Organization Splitter\n
    (10) Unwanted Image Links Remove\n
    (11) Change Datas B\W Xml Files""",
                 font=("Arial", 12), justify='center', borderwidth=10, relief="solid", padx=20, pady=20)

    # Create the input text box
    inputtxt = tk.Text(root, height=1, width=30, bg="light yellow")

    # Create the button
    display_button = tk.Button(root, height=1, width=10, text="Validate Xml",
                               command=lambda: take_input(inputtxt, root), font=("Arial", 12),
                               justify='center', borderwidth=10)

    # Grid layout
    l.grid(row=0, column=0, padx=10, pady=10)
    inputtxt.grid(row=1, column=0, padx=10, pady=10)
    display_button.grid(row=2, column=0, padx=10, pady=10)

    # Run the tkinter event loop
    root.mainloop()
