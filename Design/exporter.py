import os
import platform
import traceback
import sys

export_script = '..\..\Tools\excelExporter\exporter.py'    
generator_script = '..\..\Tools\jsonToCSharp\generator.py'
python_path = '..\..\Tools\py39\python.exe ' if platform.system() == 'Windows' else 'python '
export_folder = 'Exported'
schema_path = 'Exported\Schemas.json'
code_generate_path = '..\..\Scripts\Generated'

def generate_code(schema, outfolder):
    cmd = r' -i ' + schema
    cmd += ' -o ' + outfolder
    cmd += ' -s ' + outfolder
    cmd = python_path + generator_script + cmd
    code = os.system(cmd)
    os.remove(schema)      
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

def main():
    if len(sys.argv) <= 1:
        return
    filelist = []
    for i in range(1, len(sys.argv)):
        filelist.append(sys.argv[i])
        print(sys.argv[i])

    export(filelist)
    generate_code(schema_path, code_generate_path)

if __name__ == '__main__':
    main()