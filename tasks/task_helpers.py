import os
import yaml
import json

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


def read_data(path):
    with open(path, 'r') as f:
        return json.loads(f.read())


def write_data(path, data):
    with open(path, 'w') as f:
        f.write(json.dumps(data, indent=4))


def generate_output_filename(input_file, output_path, postfix):
    file_name, file_ext = os.path.splitext(os.path.basename(input_file))
    return os.path.join(output_path, '_'.join([file_name, postfix]) + file_ext)
