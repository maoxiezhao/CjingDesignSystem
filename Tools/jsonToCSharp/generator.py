import sys     
import os
import string
import collections
import codecs
import re
import json
import traceback
import getopt
from string import Template

TypeMapping = {
    "INT"    : "int",
    "STRING" : "string",
    "BOOL"   : "bool",
    "FLOAT"  : "float"
}

SheetTypeExportPath = {
    "Global" : "GlobalTables",
    "Design" : "DesignTables"
}

class Context:
    script_path = ''
    input_list = None  
    output_dir = '.'
    static_output_dir = '.'
    records = []
    namespace = "DesignTable"
    suffix = "Template"

class UnitMemberField:
    # public int Id { get; private set; }
    def __init__(self, name, type_):
        self.m_name = name
        self.m_type = type_

class UnitRecord:
    class_name = ""
    export_name = ""
    schema_obj = None
    member_fields = []
    sheet_type = ""

    def parse_from_json(self, jsn):
        sheet_type = jsn['sheetType'] 
        if sheet_type != "Global" and sheet_type != "Design":
            return False
        self.sheet_type = sheet_type

        self.class_name = jsn['name'] + context.suffix
        self.export_name = jsn['name']
        self.schema_obj = jsn['schema']
        if not self.schema_obj:
            return False

        for name in self.schema_obj:
            self.member_fields.append(UnitMemberField(name, self.schema_obj[name][0]))

        return True

    def write_generate_code(self, dir_path):
        if self.sheet_type == "Global":
            template_file_path = "templates/globalTable.cs.tmpl"
        else:
            template_file_path = "templates/designTable.cs.tmpl"

        template_file_path = os.path.join(context.script_path, template_file_path)
        template_file = open(template_file_path, "rb")

        if not template_file:
            raise ValueError('The template file %s dose not exists' % (root, path, r.path))
            exit(1)

        # template substitute
        template_file = template_file.read().decode('utf-8')
        tmpl = Template(template_file)

        # member fields
        member_fields_str = ""
        for member_field in self.member_fields:
            code = Template('        public ${mem_type} ${mem_name} { get; private set; }');
            if type(member_field.m_type) == list:
                type_str = TypeMapping[member_field.m_type[0]] + "[]"
            else:
                type_str = TypeMapping[member_field.m_type]

            member_fields_str += code.substitute(
                mem_type = type_str,
                mem_name = member_field.m_name,
            ) + '\n'

        # method fields
        method_fields_str = ""
        for member_field in self.member_fields:
            method_tmpl = Template('            this.${mem_name} = TableGeneratorUtility.Get(element, "${mem_name}", this.${mem_name});');
            method_fields_str += (method_tmpl.substitute(mem_name = member_field.m_name)) + '\n'

        lines = []
        lines.append(tmpl.substitute(
            namespace = context.namespace,
            tablename = self.class_name,
            member_fields = member_fields_str,
            method_fields = method_fields_str,
            export_name = self.export_name
        ).replace('\r\n', '\n'))

        # write output
        dst_path = os.path.join(dir_path, SheetTypeExportPath[self.sheet_type], self.class_name + '.cs')
        if not os.path.isdir(os.path.dirname(dst_path)):
            os.makedirs(os.path.dirname(dst_path))
            
        output_file = open(dst_path, "w", encoding='utf-8')
        output_file.writelines(lines)
        output_file.close()

        print('Write generated file %s successfully' % (dst_path))

def display_help():
    print(
    '''usage python generator.py [-p filelist] [-f outfolder] [-h]
    Arguments
        -i      : input excel files, use ',' to separate
        -o      : out folder
        -h      : print this help message and exit
    '''
    );

def write_generate_codes():
    if not os.path.isdir(context.output_dir):
        os.makedirs(context.output_dir)
    
    for record in context.records:
        record.write_generate_code(context.output_dir)

def write_static_global_tables(records):
    template_file_path = os.path.join(context.script_path, "templates/staticGlobalTables.cs.tmpl")
    template_file = open(template_file_path, "rb")
    if not template_file:
        raise ValueError('The template file %s dose not exists' % (root, path, r.path))
        exit(1)

    template_file = template_file.read().decode('utf-8')
    tmpl = Template(template_file)

    member_fields_str = ""
    method_fields_str = ""

    for record in records:
        code = Template('        public ${mem_type}Manager ${mem_name} {get; private set;} = new ${mem_type}Manager();');
        member_fields_str += code.substitute(
            mem_type = record.class_name,
            mem_name = record.export_name,
        ) + '\n'

        method_fields_str += "            " + record.export_name + ".Load();\n"
        
    lines = []
    lines.append(tmpl.substitute(
        member_fields = member_fields_str,
        method_fields = method_fields_str
    ).replace('\r\n', '\n'))

    # write output
    parent_dir = os.path.join(context.static_output_dir)
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    dst_path = os.path.join(parent_dir, "staticGlobalTables.cs")
    output_file = open(dst_path, "w", encoding='utf-8')
    output_file.writelines(lines)
    output_file.close()

    print('Write static generated file %s successfully' % (dst_path))
        

def write_static_design_tables(records):
    template_file_path = os.path.join(context.script_path, "templates/staticDesignTables.cs.tmpl")
    template_file = open(template_file_path, "rb")
    if not template_file:
        raise ValueError('The template file %s dose not exists' % (root, path, r.path))
        exit(1)

    template_file = template_file.read().decode('utf-8')
    tmpl = Template(template_file)

    member_fields_str = ""
    method_fields_str = ""

    for record in records:
        code = Template('        public ${mem_type}Manager ${mem_name} {get; private set;} = new ${mem_type}Manager();');
        member_fields_str += code.substitute(
            mem_type = record.class_name,
            mem_name = record.export_name,
        ) + '\n'

        method_fields_str += "            " + record.export_name + ".Load();\n"
        
    lines = []
    lines.append(tmpl.substitute(
        member_fields = member_fields_str,
        method_fields = method_fields_str
    ).replace('\r\n', '\n'))

    # write output
    parent_dir = os.path.join(context.static_output_dir)
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)

    dst_path = os.path.join(parent_dir, "staticDesignTables.cs")
    output_file = open(dst_path, "w", encoding='utf-8')
    output_file.writelines(lines)
    output_file.close()

    print('Write static generated file %s successfully' % (dst_path))

def write_static_tables():
    global_records = []
    design_records = []

    for record in context.records:
        if record.sheet_type == "Global":
            global_records.append(record)
        elif record.sheet_type == "Design":
            design_records.append(record)

    if len(global_records) > 0:
        write_static_global_tables(global_records)

    if len(design_records) > 0:
        write_static_design_tables(design_records)

def generate_from_jsons():
    for path in context.input_list:
        if not path:
            continue

        if os.path.isdir(path):
            raise ValueError('No such valid path of excel %s' % path)

        raw = open(path).read()
        if not raw:
            return  
        try:
            jsn = json.loads(raw)
        except:
            traceback.print_exc()
            exit(1)

        for unit in jsn:
            record = UnitRecord()
            if (record.parse_from_json(unit)):
                context.records.append(record)

    if len(context.records) > 0:
        write_generate_codes()
        write_static_tables()

def main():
    opst, args = getopt.getopt(sys.argv[1:], 'i:o:s:c:h')

    global context
    context = Context()
    context.script_path = os.path.dirname(sys.argv[0]);

    for op, v in opst:
        if  op == "-i":
            context.input_list = re.split(r'[,]+', v.strip());
        elif op == "-o":
            context.output_dir = v;
        elif op == "-s":
            context.static_output_dir = v;
        elif op == "-h":
            display_help();
            sys.exit()  

    if context.input_list == None or len(context.input_list) <= 0:
        display_help()
        exit(0)

    generate_from_jsons();
    
if __name__ == '__main__':
    main();
