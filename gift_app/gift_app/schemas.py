from marshmallow import Schema, ValidationError, fields, post_load, validates_schema

from .fields import EnumField
from .models import Citizen, Gender, ImportMessage


class CitizenSchema(Schema):
    """Схема валидации жителя Citizen.
    """

    citizen_id = fields.Integer(required=True)
    town = fields.String(required=True)
    street = fields.String(required=True)
    building = fields.String(required=True)
    apartment = fields.Integer(required=True)
    name = fields.String(required=True)
    birth_date = fields.Date(required=True, format="%d.%m.%Y")
    gender = EnumField(Gender, required=True)
    relatives = fields.List(fields.Integer, required=True)

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
        # XXX При обычном итерировании нельзя менять объект итерирования.
        while relatives_graph:
            citizen = next(iter(relatives_graph.keys()))
            citizen_relatives = relatives_graph[citizen]
            while citizen_relatives:
                relative = next(iter(citizen_relatives))
                if relative not in relatives_graph:
                    raise ValidationError(
                        f"У жителя #{citizen} не найден родственник #{relative}."
                    )
                relative_relatives = relatives_graph[relative]
                if citizen not in relative_relatives:
                    raise ValidationError(
                        f"Родственник #{relative} жителя #{citizen} не признал его."
                    )
                relative_relatives.discard(citizen)
                citizen_relatives.discard(relative)
            del relatives_graph[citizen]

    @validates_schema(pass_many=True)
    def validate_citizens_ids_unique(self, data, many=False, **kwargs):
        """У жителей должны быть уникальные citizen_id.
        """
        ids = [x['citizen_id'] for x in data]
        if len(ids) != len(set(ids)):
            raise ValidationError(f'citizen_id жителей не могут повторяться.')

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
