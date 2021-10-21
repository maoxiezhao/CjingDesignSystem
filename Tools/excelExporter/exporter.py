import sys     
import os
import string
import collections
import codecs
import re
import json
import getopt
import xlrd
from enum import Enum

# global context
class Context:
    input_list = None  
    output_dir = '.'
    records = []
    force_update = False
    implicit_write = False
    code_generate_path = None
    support_types = ('INT', 'FLOAT', 'STRING', 'BOOL', 'STRING_ID', 'RES_PATH')  # 当前支持的表格格式

class SheetType(Enum):
    UnknownTable = 0
    DesignTable  = 1
    GlobalTable  = 2

def sheet_type_to_string(sheet_type):
    if sheet_type == SheetType.DesignTable:
        return "Design"
    elif sheet_type == SheetType.GlobalTable:
        return "Global"
    else:
        return "Unknown"

class Record:
    def __init__(self, path, sheet, dir_path, export_path, export_name, export_obj, schema_obj, sheet_type):
        self.path = path 
        self.sheet = sheet 
        self.export_path = export_path 
        self.dir_path    = dir_path
        self.export_name = export_name 
        self.export_obj  = export_obj
        self.schema_obj  = schema_obj
        self.sheet_type  = sheet_type

def print_warning(string):
    print('\033[31m' + string + '\033[0m')

def print_info(string):
    pass
    ## print('\033[32m' + string + '\033[0m') 

def fillvalue(parent, name, value):
    if isinstance(parent, list):
        parent.append(value) 
    else:
        parent[name] = value

def getindex(infos, name):
    for index, item in enumerate(infos):
        if item == name:
            return index
    return -1

def isoutofdate(srcfile, tarfile):
    return not os.path.isfile(tarfile) or os.path.getmtime(srcfile) > os.path.getmtime(tarfile)


def display_help():
    print(
    '''usage python exporter.py [-p filelist] [-f outfolder] [-c codeGeneratePath] [-h|-w|-f]
    Arguments
        -i      : input_list excel files, use ',' to separate
        -o      : out folder
        -h      : print this help message and exit
        -f      ：force update exported ignoring time diff
        -c      : code generated path (dose not generate if is null)
        -w      : implicit write dir according by sheetType
    '''
    );

def parse_sheet_type(sheet):
    sheet_type = SheetType.UnknownTable;
    titles = sheet.row_values(0)
    if getindex(titles, "DesignTable") != -1:
        sheet_type = SheetType.DesignTable
    elif getindex(titles, "GlobalTable") != -1:
        sheet_type = SheetType.GlobalTable
    return sheet_type

def parse_type(type_):
    if type_[-2] == '[' and type_[-1] == ']':
        return 'list'
    if type_ in context.support_types:
        return type_
    raise ValueError('%s is not a invalid type' % type_)

def parse_list_value(parent, type_, name, value, is_scheme):
    typename = parse_type(type_[:-2])
    # TODO: 支持多维数组
    list_ = []
    if is_scheme:
        parse_base_value(list_, typename, name, None, is_scheme)
        list_ = [list_[0]]
    else:
        values = value.strip('[]').split(',')
        for v in values:
            parse_base_value(list_, typename, name, v, is_scheme)

    fillvalue(parent, name, list_)

def parse_base_value(parent, type_, name, value, is_scheme):
    typename = parse_type(type_)
    if is_scheme:
        fillvalue(parent, name, [typename])
        return

    if typename == 'INT':
        value = int(float(value))
    elif typename == 'FLOAT':
        value = float(value)   
    elif typename == "STRING":
        value = str(value).replace('\0', ',')         
    elif typename == "BOOL":
        try:
            value = int(float(value))
            value = False if value == 0 else True 
        except ValueError:
            value = value.lower() 
            if value in ('false', 'no', 'off'):
                value = False
            elif value in ('true', 'yes', 'on'):
                value = True
            else:    
                raise ValueError('%s is a invalid bool value' % value) 
    elif typename == "STRING_ID":
        value = str(value).replace('\0', ',')    
    elif typename == "RES_PATH":
        value = str(value).replace('\0', ',')    

    fillvalue(parent, name, value)

def parse_value(item, type_, name, value, is_scheme):
    typename = parse_type(type_)
    if typename == 'list':
        parse_list_value(item, type_, name, value, is_scheme)
    else:
        parse_base_value(item, typename, name, value, is_scheme)
    pass

def parse_design_table(path, sheet):
    # Design Table Format:
    # row 0: DesignTable
    # row 1: Name
    # row 2: Type
    # row 3: comment
    names = sheet.row_values(1)
    types = sheet.row_values(2)

    schema_obj = collections.OrderedDict()
    # collect header infos
    header_infos = []
    try:
        for col_index in range(sheet.ncols):
            name_ = str(names[col_index]).strip()
            if name_ == '#':
                continue

            type_ = str(types[col_index]).strip()
            if len(type_) <= 0 or len(name_) <= 0:
                raise ValueError('%s or %s is a illegal identifier' % (type_, name_))

            header_infos.append((type_, name_, col_index))

            # 是否生成Schema代码文件
            if context.code_generate_path:
                if type_ and name_:
                    parse_value(schema_obj, type_, name_, None, True)  

    except Exception as e: 
        e.args += ('%s has a error, %s at %d column in %s' % (sheet.name, (type_, name_), col_index + 1, path), '')
        raise e

    # collect items
    items = []
    need_export = next((i for i in header_infos if i[0] and i[1]), False)
    if need_export:
        try:
            # parse row from 4th row
            for row_index in range(4, sheet.nrows):
                item = collections.OrderedDict()
                row = sheet.row_values(row_index)
                first_string = str(row[0]).strip()

                # 如果第一个字符是#或者为空则为注释行
                if not first_string or first_string[0] == '#':
                    continue
            
                # 解析当前行每列的数据
                for col_index in range(sheet.ncols):
                    type_ = header_infos[col_index][0]
                    name_ = header_infos[col_index][1]
                    value_ = str(row[col_index])

                    if row[col_index] == None and value_ == "":
                        raise ValueError('Has a null value.') 
                    
                    parse_value(item, type_, name_, value_, False)  

                if item:
                    items.append(item)
                    
        except Exception as e: 
            e.args += ('%s has a error, %s at %d column in %s' % (sheet.name, (type_, name_), col_index + 1, path) , '')
            raise e

    return items, schema_obj

def parse_global_table(path, sheet):
    # Global Table Format:
    # row 0: Name(col 1) type(col 2) value(col 3) 
    titles = sheet.row_values(1)
    name_index  = getindex(titles, "name")
    type_index  = getindex(titles, "type")
    value_index = getindex(titles, "value")

    if name_index == -1 or value_index == -1 or type_index == -1:
        raise ValueError('%s:%s is a invalid globalTable' % (path, sheet.name))
       
    schema_obj = collections.OrderedDict()
    data_obj = collections.OrderedDict()
    try:
        # parse row from 4th row
        for row_index in range(2, sheet.nrows):
            row = sheet.row_values(row_index)
           
            # 如果第一个字符是#或者为空则为注释行
            first_string = str(row[0]).strip()
            if not first_string or first_string[0] == '#':
                continue

            # 解析当前行的数据
            name_  = str(row[name_index]).strip()
            value_ = str(row[value_index]).strip()
            type_  = str(row[type_index]).strip()
            if name_ and type_ and value_:
                parse_value(data_obj, type_, name_, value_, False)  
      
            # 是否生成Schema代码文件
            if context.code_generate_path:
                if type_ and name_:
                    parse_value(schema_obj, type_, name_, None, True)  
                
    except Exception as e: 
        e.args += ('%s has a error, %s at %d column in %s' % (sheet.name, (type_, name_), row_index + 1, path) , '')
        raise e

    return data_obj, schema_obj

def write_files(context):
    # write talbe files
    for r in context.records:
        if r.export_obj:
            if not os.path.isdir(r.dir_path):
                os.makedirs(r.dir_path)

            jsonstr = json.dumps(r.export_obj, ensure_ascii = False, indent = 2)
            with codecs.open(r.export_path, 'w', 'utf-8') as f:
                f.write(jsonstr)

            print_info('Write export file %s from %s in %s successfully' % (r.path, r.sheet.name, r.export_path))

    # 统一写入schema文件
    schemas = []
    for r in context.records:
        if r.schema_obj and context.code_generate_path:
            schemas.append({'name' : r.export_name, 'sheetType' : sheet_type_to_string(r.sheet_type), 'schema' : r.schema_obj})
    if len(schemas) > 0:
        dir_path = os.path.dirname(context.code_generate_path)
        if dir_path and not os.path.isdir(dir_path):
            os.makedirs(dir_path)

        jsonstr = json.dumps(schemas, ensure_ascii = False, indent = 2)
        with codecs.open(context.code_generate_path, 'w', 'utf-8') as f:
            f.write(jsonstr)

        print_info('Write schema file %s successfully' % (context.code_generate_path))

def export_excel(context, path):
    data = xlrd.open_workbook(path)

    available_count = 0
    for sheet in data.sheets():
        # 检查当前sheet是否需要导出，检查sheet name中是否包含|
        p = re.search('\|[' + string.whitespace + ']*(_|[a-zA-Z]\w+)', sheet.name)
        if p == None or p.group(1) == None:
            continue;
        available_count = available_count + 1

        export_name = p.group(1);
        sheet_type = parse_sheet_type(sheet)
        if sheet_type != SheetType.UnknownTable:
            # 根据SheetType获取导出路径
            if context.implicit_write:
                if sheet_type == SheetType.DesignTable:
                    dir_path = os.path.join(context.output_dir, "DesignTable")
                else:
                    dir_path = os.path.join(context.output_dir, "GlobalTable")
            else:
                dir_path = os.path.join(context.output_dir)
            export_path = os.path.join(dir_path, export_name + '.json')

            # 检查当前表名是否已经导出
            r = next((r for r in context.records if r.export_name == export_name), False)
            if r:
                raise ValueError('%s in %s is already defined in %s' % (export_name, path, r.export_path))
            
            # 仅当原数据表修改后才去分析表
            if not context.force_update and not isoutofdate(path, export_path):
                continue

            # 根据sheet_type分析对应的表项
            if sheet_type == SheetType.DesignTable:
                export_obj, schema_obj = parse_design_table(path, sheet)
            else:
                export_obj, schema_obj = parse_global_table(path, sheet)

            # 记录当前导出项
            context.records.append(Record(path, sheet, dir_path, export_path, export_name, export_obj, schema_obj, sheet_type))

    # write exported files
    write_files(context)
    

def export_excels(context):
    for path in context.input_list:
        if not path:
            continue

        if os.path.isdir(path):
            raise ValueError('No such valid path of excel %s' % path)

        # 检查文件是否已经导出
        r = next((r for r in context.records if r.path == path), False)
        if r:
            raise ValueError('%s is already export' % path)

        export_excel(context, path)

def main():
    opst, args = getopt.getopt(sys.argv[1:], 'i:o:c:fwh')

    global context
    context = Context()

    for op, v in opst:
        if op == "-i":
            context.input_list = re.split(r'[,]+', v.strip());
        elif op == "-o":
            context.output_dir = v;
        elif op == "-c":
            context.code_generate_path = v
        elif op == "-f":
            context.force_update = True
        elif op == "-w":
            context.implicit_write = True
        elif op == "-h":
            display_help();
            sys.exit()  

    if context.input_list == None or len(context.input_list) <= 0:
        display_help()
        exit(0)

    export_excels(context);
    
if __name__ == '__main__':
    os.system('')
    main();
