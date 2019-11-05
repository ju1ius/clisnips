from .field import Field
from .flag import FlagField
from .path import PathField
from .range import RangeField
from .select import SelectField
from .text import TextField
from ...strfmt.doc_nodes import Documentation, Parameter, ValueList, ValueRange


def field_from_documentation(field_name: str, doc: Documentation) -> Field:
    param = doc.parameters.get(field_name)
    if not param:
        label = f'<b>{field_name}</b>'
        if field_name.startswith('-'):
            return FlagField(label, flag=field_name)
        return TextField(label)
    return _field_from_param(param)


def _field_from_param(param: Parameter) -> Field:
    label = _label_from_param(param)
    type_hint = param.typehint
    value_hint = param.valuehint
    default = ''
    if isinstance(value_hint, ValueRange):
        return RangeField(
            label,
            start=value_hint.start,
            end=value_hint.end,
            step=value_hint.step,
            default=value_hint.default
        )
    if isinstance(value_hint, ValueList):
        if len(value_hint) > 1:
            return SelectField(label, options=value_hint.values, default=value_hint.default)
        default = str(value_hint.values[0])
    if type_hint in ('path', 'file', 'dir'):
        return PathField(label, mode=type_hint, default=default)
    if type_hint == 'flag':
        return FlagField(label, flag=param.name)
    return TextField(label, default=default)


def _label_from_param(param: Parameter) -> str:
    hint = f'(<i>{param.typehint}</i>)' if param.typehint else ''
    text = param.text.strip() if param.text else ''
    return f'<b>{param.name}</b> {hint} {text}'
