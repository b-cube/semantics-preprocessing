import yaml


def import_yaml_configs(config_paths):
    '''
    merge a set of yaml config files so we can maintain
    one set of identify structures for a protocol
    '''

    def _read(config_path):
        with open(config_path, 'r') as f:
            y = yaml.load(f.read())

        return y

    # the configs are just big lists
    config = []
    for config_path in config_paths:
        config += _read(config_path)

    return config
