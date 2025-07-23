import yaml
import importlib

from factories.config import Config

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

def import_class(path):
    mod_name, cls_name = path.rsplit(".", 1)
    mod = importlib.import_module(mod_name)
    return getattr(mod, cls_name)

def resolve(val, all_objects):
    if isinstance(val, str) and val in all_objects:
        return all_objects[val]
    elif isinstance(val, list):
        return [resolve(v, all_objects) for v in val]
    return val

from inspect import signature

def instantiate_instances(section, override_values, all_objects):
    instantiated = {}
    pending = {}

    for name, spec in section.items():
        cls = import_class(spec["class"])
        params = spec.get("params", {}).copy()

        # Apply only valid overrides — match to constructor args
        init_params = signature(cls).parameters
        valid_overrides = {
            k: v for k, v in override_values.items() if k in init_params
        }

        combined = {**params, **valid_overrides}

        try:
            resolved = {k: resolve(v, all_objects) for k, v in combined.items()}
            obj = cls(**resolved)
            instantiated[name] = obj
            all_objects[name] = obj
        except Exception:
            pending[name] = (cls, combined)

    for name, (cls, combined) in pending.items():
        resolved = {k: resolve(v, all_objects) for k, v in combined.items()}
        obj = cls(**resolved)
        instantiated[name] = obj
        all_objects[name] = obj

    return instantiated

def build_config(yaml_config):
    config_section = yaml_config.get("config", {})

    # Keys that refer to which instances to load
    instance_keys = {"vehicles", "people", "time_series"}

    # Used as constructor param overrides
    override_keys = {
        k: v for k, v in config_section.items() if k not in instance_keys
    }

    # Extra fields (like csv_intake) to store in final config
    extra_config_fields = {
        k: v for k, v in config_section.items()
        if k not in instance_keys and k not in override_keys
    }

    all_objects = {}
    all_vehicles = instantiate_instances(yaml_config.get("vehicles", {}), override_keys, all_objects)
    all_people = instantiate_instances(yaml_config.get("people", {}), override_keys, all_objects)
    all_time_series = instantiate_instances(yaml_config.get("time_series", {}), override_keys, all_objects)

    selected_vehicles = {name: all_vehicles[name] for name in config_section.get("vehicles", [])}
    selected_people = {name: all_people[name] for name in config_section.get("people", [])}
    selected_time_series = {name: all_time_series[name] for name in config_section.get("time_series", [])}

    from factories.config import Config
    return Config(
        vehicles=selected_vehicles,
        people=selected_people,
        time_series=selected_time_series,
        **extra_config_fields  # Pass through csv_intake, etc.
    )



# if __name__ == "__main__":
#     cfg = load_yaml("config.yaml")
#     config = build_config(cfg)

#     config.print_config()

#     for name, v in config.vehicles.items():
#         print(f"{name}: {v.make} {v.model}, year={v.year}")

#     for name, p in config.people.items():
#         print(f"{name}: {p.name}, car={p.car.model}")
