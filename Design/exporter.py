import os
import platform
import traceback
import sys
import os
import platform
import glob

project_path = "..\\"
project_name = "CBA"
export_script = '..\Tools\excelExporter\exporter.py'    
generator_script = '..\Tools\jsonToCSharp\generator.py'
python_path = '..\Tools\py39\python.exe ' if platform.system() == 'Windows' else 'python '
export_folder =  project_path + '\\' + project_name + '\\' + 'Exported'
schema_path = 'Exported\Schemas.json'
code_generate_path = project_path + '\\' + project_name + '\\' + 'Scripts\Generated'
table_src_dirs = ('DesignTables', 'GlobalTables')

def generate_code(schema, outfolder):
    cmd = r' -i ' + schema
    cmd += ' -o ' + outfolder
    cmd += ' -s ' + outfolder
    cmd = python_path + generator_script + cmd
    code = os.system(cmd)
    os.remove(schema)    
    os.rmdir(os.path.dirname(schema))
    if code != 0:
        raise ValueError('Export excel fail')
        input()

def export(filelist):
    cmd = r' -i "' + ','.join(filelist) + '" -o ' + export_folder
    cmd += ' -c ' + schema_path + ''
    cmd += ' -f -w'
    cmd = python_path + export_script + cmd
    code = os.system(cmd)
    if code != 0:
        raise ValueError('Export excel fail')
        input()

def scan_directory():
    filelist = []
    for table_src_dir in table_src_dirs:
        filelist = filelist + sorted(glob.glob(table_src_dir + "/**/*.xls", recursive=True), reverse=False)
    for item in filelist:
        print(item)
    return filelist

def main():
    if len(sys.argv) <= 1:
        return
    filelist = []
    if sys.argv[1] == '-a':
        filelist = scan_directory()
    else:
        for i in range(1, len(sys.argv)):
            filelist.append(sys.argv[i])

    if len(filelist) > 0:
        export(filelist)
        generate_code(schema_path, code_generate_path)

if __name__ == '__main__':
    main()