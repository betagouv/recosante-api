from marshmallow import fields, ValidationError
import typing

class TempList(fields.List):
    def _serialize(self, value: typing.Any, attr: str, obj: typing.Any, **kwargs):
        if value:
            return [self.inner._serialize(value, attr, obj, **kwargs)]
        return value

    def _deserialize(self, value: typing.Any, attr: typing.Optional[str], data: typing.Optional[typing.Mapping[str, typing.Any]], **kwargs):
        if type(value) == list:
            if len(value) == 0:
                return None
            elif len(value) == 1:
                return self.inner.deserialize(value[0])
            else:
                raise ValidationError("There can be just one element for this field")
        return value