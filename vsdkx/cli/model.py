import yaml
from minio import Minio, S3Error

from vsdkx.cli.credential import read_secret
from vsdkx.cli.global_constants import NAME_REGEX, POSTFIX_MODEL
import re, os

from vsdkx.cli.util import install, create_folder, modify_app, uninstall
from vsdkx.cli.weight import download_weight, remove_weight


def add_model(args):
    """
    Add a model driver to current project

    Args:
        args: args[0] is the name of the model and args[1] is optional and is
        the name of the weight file that we want to use for this model driver
    """
    endpoint, access_key, secret_key, region, secure = read_secret()
    model = args[0]
    print(f"Adding model {model} ...")
    assert re.match(NAME_REGEX, model), \
        "model name is not right"
    install(f"vsdkx-model-{model}")
    create_folder("vsdkx")
    create_folder("vsdkx/model")
    current_profile = "vsdkx/model/profile.yaml"
    bucket_name = f"{model}{POSTFIX_MODEL}"
    minio = Minio(endpoint, access_key, secret_key, region=region,
                  secure=secure)
    try:
        response = minio.get_object(bucket_name, "profile.yaml")
        dict1 = yaml.full_load(response)
        dict2 = {}
        if os.path.exists(current_profile):
            with open(current_profile, "r") as file:
                dict2 = yaml.full_load(file)
        if dict2 is None:
            dict2 = {}
        merged = {**dict1, **dict2}
        with open(current_profile, 'w') as file:
            yaml.dump(merged, file)
        modify_app(f"model-{model}")
        print(f"{model} added")
        download_weight(args)
    except S3Error as e:
        print(e)


def remove_model(args):
    """
    Removes model driver from current project

    Args:
        args: args[0] is the name of the model driver
    """
    model = args[0]
    uninstall(f"vsdkx-model-{model}")
    current_profile = "vsdkx/model/profile.yaml"
    if os.path.exists(current_profile):
        with open(current_profile, "r") as file:
            data = yaml.full_load(file)
            data.pop(model)
        if data is not None:
            with open(current_profile, "w") as file:
                yaml.dump(data, file)
    modify_app(f"model-{model}", True)
    remove_model_from_setting(model)
    remove_weight(args)


def remove_model_from_setting(name):
    """
    Remove model section from vsdkx/settings.yaml for specific model name

    Args:
        name: the name of the model driver
    """
    settings_path = "vsdkx/settings.yaml"
    if os.path.exists(settings_path):
        with open(settings_path, "r") as file:
            settings = yaml.full_load(file)
        if "model" in settings:
            if "profile" in settings["model"]:
                if settings["model"]["profile"] == name:
                    settings.pop("model")
                    with open(settings_path, "w") as file:
                        yaml.dump(settings, file)
