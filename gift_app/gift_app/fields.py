from marshmallow import fields, validate


class EnumField(fields.Field):
    """(де-)сериализация enum.Enum значений.
    """

    def __init__(self, enum, *a, **kw):
        self.__enum = enum
        self.__valid_names = [x.name for x in enum]
        kw.setdefault("validate", []).append(validate.OneOf([x.name for x in enum]))
        super().__init__(*a, **kw)

    def _serialize(self, value, attr, obj):
        assert value.name in self.__valid_names
        return str(value.name)

    def deserialize(self, value, attr=None, data=None, **kwargs):
        value = super().deserialize(value, attr=attr, data=data, **kwargs)
        enum_value = getattr(self.__enum, value)
        return enum_value
