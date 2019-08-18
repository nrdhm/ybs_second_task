import datetime as dt
from marshmallow import (
    Schema,
    ValidationError,
    fields,
    post_load,
    validate,
    validates_schema,
)
from functools import partial

from .fields import EnumField
from .models import Citizen, Gender, ImportMessage


NonEmptyString = partial(
    fields.String, required=True, validate=[validate.Length(min=1, max=257)]
)
NonNegativeInteger = partial(
    fields.Integer, required=True, validate=[validate.Range(min=0)]
)


def _vaildate_birth_date(birth_date: dt.date):
    if birth_date >= dt.date.today():
        raise ValidationError("Дата рождения должна быть меньше текущей даты.")


class CitizenSchema(Schema):
    """Схема валидации жителя Citizen.
    """

    citizen_id = NonNegativeInteger()
    town = NonEmptyString()
    street = NonEmptyString()
    building = NonEmptyString()
    apartment = NonNegativeInteger()
    name = NonEmptyString()
    birth_date = fields.Date(
        required=True, format="%d.%m.%Y", validate=[_vaildate_birth_date]
    )
    gender = EnumField(Gender, required=True)
    relatives = fields.List(NonNegativeInteger(), required=True)

    @validates_schema(pass_many=True)
    def validate_relatives(self, data, many=False, **kwargs):
        """Проверить валидность списка родни у всех жителей.
        Айди родственников должны быть в наборе жителей.
        Родственные связи должны быть двусторонними.
        У одного жителя не могут родственники не могут повторяться.
        """
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
        ids = [x["citizen_id"] for x in data]
        if len(ids) != len(set(ids)):
            raise ValidationError(f"citizen_id жителей не могут повторяться.")

    @post_load(pass_many=True)
    def make_citizens(self, data, many=False, **kwargs):
        """Создать и вернуть модели жителей из валидированных данных.
        """
        relatives_graph = {x["citizen_id"]: set(x["relatives"]) for x in data}
        citizen_for_id = {}
        # Сначала создать всех жителей.
        for x in data:
            citizen = Citizen(
                citizen_id=x["citizen_id"],
                town=x["town"],
                street=x["street"],
                building=x["building"],
                apartment=x["apartment"],
                name=x["name"],
                birth_date=x["birth_date"],
                gender=x["gender"],
            )
            citizen_for_id[citizen.citizen_id] = citizen
        # Потом установить родственные связи.
        for citizen_id, relative_ids in relatives_graph.items():
            citizen = citizen_for_id[citizen_id]
            for relative_id in relative_ids:
                relative = citizen_for_id[relative_id]
                citizen.relatives.append(relative)
        return citizen_for_id.values()


class ImportsSchema(Schema):
    citizens = fields.Nested(CitizenSchema(many=True), required=True)

    @post_load
    def make_import_message(self, data, **kw):
        return ImportMessage(citizens=data["citizens"])
