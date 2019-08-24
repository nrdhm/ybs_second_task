import datetime as dt
from functools import partial

from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates,
    validates_schema,
)

from .fields import EnumField
from .models import Citizen, Gender, ImportMessage

NonEmptyString = partial(fields.String, validate=[validate.Length(min=1, max=257)])
NonNegativeInteger = partial(fields.Integer, validate=[validate.Range(min=0)])


def _vaildate_birth_date(birth_date: dt.date):
    if birth_date >= dt.date.today():
        raise ValidationError("Дата рождения должна быть меньше текущей даты.")


BirthDate = partial(fields.Date, format="%d.%m.%Y", validate=[_vaildate_birth_date])


class CitizenSchema(Schema):
    """Схема валидации жителя Citizen.
    """

    citizen_id = NonNegativeInteger(required=True)
    town = NonEmptyString(required=True)
    street = NonEmptyString(required=True)
    building = NonEmptyString(required=True)
    apartment = NonNegativeInteger(required=True)
    name = NonEmptyString(required=True)
    birth_date = BirthDate(required=True)
    gender = EnumField(Gender, required=True)
    relatives = fields.List(NonNegativeInteger(), required=True)

    @validates_schema(pass_many=True)
    def validate_relatives(self, data, many=False, **kwargs):
        """Проверить валидность списка родни у всех жителей.
        Айди родственников должны быть в наборе жителей.
        Родственные связи должны быть двусторонними.
        У одного жителя не могут родственники не могут повторяться.
        """
        if not many:
            return data
        relatives_graph = {}
        for x in data:
            relatives = set(x["relatives"])
            citizen_id = x["citizen_id"]
            if len(relatives) != len(x["relatives"]):
                raise ValidationError(
                    f"У жителя #{citizen_id} повторяются родственники: {x['relatives']}"
                )
            relatives_graph[citizen_id] = relatives
        for citizen, citizen_relatives in relatives_graph.items():
            for relative in citizen_relatives:
                if relative not in relatives_graph:
                    raise ValidationError(
                        f"У жителя #{citizen} не найден родственник #{relative}."
                    )
                relative_relatives = relatives_graph[relative]
                if citizen not in relative_relatives:
                    raise ValidationError(
                        f"Родственник #{relative} жителя #{citizen} не признает его своим."
                    )

    @validates_schema(pass_many=True)
    def validate_citizens_ids_unique(self, data, many=False, **kwargs):
        """У жителей должны быть уникальные citizen_id.
        """
        if not many:
            return data
        ids = [x["citizen_id"] for x in data]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"citizen_id жителей не могут повторяться.")

    @post_load
    def make_citizen(self, data, **kw):
        return Citizen(**data)


class CitizenUpdateSchema(Schema):
    town = NonEmptyString()
    street = NonEmptyString()
    building = NonEmptyString()
    apartment = NonNegativeInteger()
    name = NonEmptyString()
    birth_date = BirthDate()
    gender = EnumField(Gender)
    relatives = fields.List(NonNegativeInteger())

    @validates("relatives")
    def validate_relatives(self, relatives):
        if len(relatives) != len(set(relatives)):
            raise ValidationError(f"Список родственников неуникален")


class ImportsSchema(Schema):
    citizens = fields.List(fields.Nested(CitizenSchema), required=True)

    @post_load
    def make_import_message(self, data, **kw):
        return ImportMessage(citizens=data["citizens"])


class TownAgeStatSchema(Schema):
    town = fields.String()
    p50 = fields.Float()
    p75 = fields.Float()
    p99 = fields.Float()
