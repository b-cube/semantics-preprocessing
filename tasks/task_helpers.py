import os
import yaml
import json
from lib.yaml_configs import import_yaml_configs

'''
general task methods

mainly, parse the yaml configuration file
'''


def parse_yaml(yaml_file):
    with open(yaml_file, 'r') as f:
        y = yaml.load(f.read())
    return y


def extract_task_config(yaml_config, task):
    return yaml_config.get(task, {})


def run_init(config):
    init_tasks = config.get('init', {})
    if not init_tasks:
        return

    if 'clear_output_directories' in init_tasks:
        # get the output dirs and delete any files
        tasks = {k: v for k, v in config.iteritems() if k != 'init'}
        output_dirs = [task['output_directory'] for task in tasks.values()
                       if 'output_directory' in task]
        for output_dir in output_dirs:
            clear_directory(output_dir)


def read_data(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


def write_data(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))


def generate_output_filename(input_file, output_path, postfix):
    file_name, file_ext = os.path.splitext(os.path.basename(input_file))
    return os.path.join(output_path, '_'.join([file_name, postfix]) + file_ext)


def clear_directory(directory):
    for d in os.walk(directory):
        subdir = d[0]
        files = d[2]
        for f in files:
            os.remove(os.path.join(subdir, f))


def load_yamls(yamls):
    return import_yaml_configs(yamls)
