from datetime import datetime

from utils.time_conversion import START_END_TIME_FORMAT
import logging

logger = logging.getLogger(__name__)


class Config:
    def __init__(self, mode, start_time, end_time, vehicles, people, time_series, **extra_fields):
        self.mode = mode
        self.start_time = start_time
        self.end_time = end_time
        self.vehicles = vehicles
        self.people = people
        self.time_series = time_series

        # Dynamically assign any extra config-only fields
        for key, value in extra_fields.items():
            setattr(self, key, value)

        self.checks()


    def checks(self):
        # Validate datetime formats
        try:
            datetime.strptime(self.start_time, START_END_TIME_FORMAT)
            datetime.strptime(self.end_time, START_END_TIME_FORMAT)
        except ValueError:
            msg = (
                f"start_time and end_time must be in 'YYYY-MM-DD HH:MM' format. "
                f"Got: start_time='{self.start_time}', end_time='{self.end_time}'"
            )
            logger.error(msg)
            raise ValueError(msg)

        # Validate time_series is a list
        if not isinstance(self.time_series, list):
            msg = f"time_series must be a list, got: {type(self.time_series).__name__}"
            logger.error(msg)
            raise TypeError(msg)

        # Validate mode
        valid_modes = {"backtest", "live"}
        if self.mode not in valid_modes:
            msg = f"Invalid mode '{self.mode}'. Must be one of: {valid_modes}"
            logger.error(msg)
            raise ValueError(msg)


    def to_string(self):
        return self._build_string(self)

    def _build_string(self, obj, indent=0):
        pad = "  " * indent
        lines = []

        if isinstance(obj, dict):
            if not obj:
                lines.append(f"{pad}(empty dict)")
            else:
                for key, value in obj.items():
                    lines.append(f"{pad}{key}:")
                    lines.append(self._build_string(value, indent + 1))

        elif isinstance(obj, list):
            if not obj:
                lines.append(f"{pad}(empty list)")
            else:
                for i, item in enumerate(obj):
                    lines.append(f"{pad}- [{i}]:")
                    lines.append(self._build_string(item, indent + 1))

        elif hasattr(obj, '__dict__'):
            attrs = vars(obj)
            if not attrs:
                lines.append(f"{pad}{obj}")
            else:
                for key, value in attrs.items():
                    lines.append(f"{pad}{key}:")
                    lines.append(self._build_string(value, indent + 1))

        else:
            lines.append(f"{pad}{obj}")

        return "\n".join(lines)

def print_config(self) -> str:
    def format_obj(obj, indent=2, seen=None):
        if seen is None:
            seen = {}

        pad = ' ' * indent
        lines = []

        obj_id = id(obj)
        if obj_id in seen:
            lines.append(f"{pad}<{seen[obj_id]}>")
            return lines

        if isinstance(obj, (str, int, float, bool, type(None))):
            lines.append(f"{pad}{obj}")
            return lines

        seen[obj_id] = type(obj).__name__

        if isinstance(obj, dict):
            for key, value in obj.items():
                lines.append(f"{pad}{key}:")
                lines.extend(format_obj(value, indent + 2, seen))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                lines.append(f"{pad}-")
                lines.extend(format_obj(item, indent + 2, seen))
        else:
            # Handle dynamic or unknown object fields
            attributes = {
                k: v for k, v in vars(obj).items()
                if not k.startswith("_") and not callable(v)
            }

            for attr, value in attributes.items():
                lines.append(f"{pad}{attr}:")
                lines.extend(format_obj(value, indent + 2, seen))

        return lines

    header = f"{self.__class__.__name__}:"
    body = format_obj(self, indent=2)
    return "\n".join([header] + body)
