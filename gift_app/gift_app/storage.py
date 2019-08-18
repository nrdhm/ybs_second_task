from typing import List

import aiopg.sa
import sqlalchemy as sa

from .config import Config
from .errors import InvalidUsage
from .models import Citizen, Gender, ImportMessage


class Storage:
    def __init__(self, config: Config):
        self.config = config
        self._engine = None

    async def initialize(self):
        DSN = "postgresql://{username}:{password}@{host}:{port}/{db_name}"
        engine = await aiopg.sa.create_engine(
            DSN.format(
                username=self.config.db.username,
                password=self.config.db.password,
                host=self.config.db.host,
                port=self.config.db.port,
                db_name=self.config.db.name,
            )
        )
        self._engine = engine
        return self

    @property
    def engine(self) -> aiopg.sa.Engine:
        if not self._engine:
            raise RuntimeError("Storage is not initialized")
        return self._engine

    async def save_citizen(self, import_id: int, citizen: Citizen) -> bool:
        async with self.engine.acquire() as conn:  # type: aiopg.sa.SAConnection
            async with conn.begin():
                if not await self._import_exists(conn, import_id):
                    await self._create_import(conn, import_id)
                await self._save_citizen(conn, import_id, citizen)
                return True

    async def retrieve_citizen(self, import_id: int, citizen_id: int) -> Citizen:
        async with self.engine.acquire() as conn:  # type: aiopg.sa.SAConnection
            return await self._retrieve_citizen(conn, import_id, citizen_id)

    async def retrieve_citizen_relatives(
        self, import_id: int, citizen_id: int
    ) -> List[Citizen]:
        async with self.engine.acquire() as conn:  # type: aiopg.sa.SAConnection
            r = await conn.execute(
                relative_table.select()
                .where(relative_table.c.import_id == import_id)
                .where(relative_table.c.citizen_id == citizen_id)
            )
            relative_ids = []
            async for row in r:
                relative_ids.append(row["relative_citizen_id"])
            relatives = await self._retrieve_citizens(conn, import_id, relative_ids)
            return relatives

    async def import_citizens(self, import_message: ImportMessage) -> int:
        async with self.engine.acquire() as conn:  # type: aiopg.sa.SAConnection
            async with conn.begin():
                import_id = await self._next_import_id(conn)
                await self._create_import(conn, import_id)
                for citizen in import_message.citizens:
                    await self._save_citizen(conn, import_id, citizen)
                return import_id

    async def _save_citizen(
        self, conn: aiopg.sa.SAConnection, import_id: int, citizen: Citizen
    ) -> bool:
        await conn.execute(
            citizen_table.insert().values(
                import_id=import_id,
                citizen_id=citizen.citizen_id,
                town=citizen.town,
                street=citizen.street,
                building=citizen.building,
                apartment=citizen.apartment,
                name=citizen.name,
                birth_date=citizen.birth_date,
                gender=citizen.gender,
            )
        )
        for relative in citizen.relatives:
            await conn.execute(
                relative_table.insert().values(
                    import_id=import_id,
                    citizen_id=citizen.citizen_id,
                    relative_citizen_id=relative.citizen_id,
                )
            )
        return True

    async def _retrieve_citizen(
        self, conn: aiopg.sa.SAConnection, import_id: int, citizen_id: int
    ) -> Citizen:
        r = await conn.execute(
            citizen_table.select()
            .where(citizen_table.c.citizen_id == citizen_id)
            .where(citizen_table.c.import_id == import_id)
            .limit(1)
        )
        if not r.rowcount:
            raise InvalidUsage.not_found(
                f"Житель #{citizen_id} из набора #{import_id} не найден"
            )
        row = await r.fetchone()
        citizen = self._citizen_from_row(row)
        return citizen

    def _citizen_from_row(self, row: aiopg.sa.connection.ResultProxy) -> Citizen:
        citizen = Citizen(
            citizen_id=row["citizen_id"],
            town=row["town"],
            street=row["street"],
            building=row["building"],
            apartment=row["apartment"],
            name=row["name"],
            birth_date=row["birth_date"],
            gender=row["gender"],
        )
        return citizen

    async def _retrieve_citizens(
        self, conn: aiopg.sa.SAConnection, import_id: int, citizen_ids: List[int]
    ) -> List[Citizen]:
        r = await conn.execute(
            citizen_table.select()
            .where(citizen_table.c.import_id == import_id)
            .where(citizen_table.c.citizen_id.in_(citizen_ids))
        )
        if r.rowcount != len(citizen_ids):
            # Кто-то из списка не был найден в базе данных.
            assert r.rowcount < len(citizen_ids)
            ids = set(citizen_ids)
            async for row in r:
                ids.remove(row["id"])
            raise InvalidUsage.not_found(
                f"Некоторые жители не были найдены: {''.join(str(x) for x in ids)}"
            )
        citizens = []
        async for row in r:
            citizen = self._citizen_from_row(row)
            citizens.append(citizen)
        return citizens

    async def _import_exists(self, conn: aiopg.sa.SAConnection, import_id: int) -> bool:
        r = await conn.scalar(
            import_table.select().where(import_table.c.import_id == import_id).limit(1)
        )
        return bool(r)

    async def _create_import(self, conn: aiopg.sa.SAConnection, import_id: int) -> int:
        r = await conn.execute(import_table.insert().values(import_id=import_id))
        return bool(r.rowcount)

    async def _next_import_id(self, conn: aiopg.sa.SAConnection) -> int:
        t = await conn.scalar(sa.select([import_seq.next_value()]))
        return t


convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

meta = sa.MetaData(naming_convention=convention)

gender_enum = sa.Enum(Gender, name="citizen_gender")

import_seq = sa.Sequence("import_seq")

import_table = sa.Table(
    "import", meta, sa.Column("import_id", sa.Integer, primary_key=True)
)

citizen_table = sa.Table(
    "citizen",
    meta,
    sa.Column("import_id", sa.Integer, sa.ForeignKey("import.import_id")),
    sa.Column("citizen_id", sa.Integer),
    sa.Column("town", sa.String, nullable=False),
    sa.Column("street", sa.String, nullable=False),
    sa.Column("building", sa.String, nullable=False),
    sa.Column("apartment", sa.Integer, nullable=False),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("birth_date", sa.Date, nullable=False),
    sa.Column("gender", gender_enum, nullable=False),
    sa.PrimaryKeyConstraint("import_id", "citizen_id"),
)

relative_table = sa.Table(
    "relative",
    meta,
    sa.Column("import_id", sa.Integer, primary_key=True),
    sa.Column("citizen_id", sa.Integer, primary_key=True),
    sa.Column("relative_citizen_id", sa.Integer, primary_key=True),
    sa.ForeignKeyConstraint(
        ["citizen_id", "import_id"],
        ["citizen.citizen_id", "citizen.import_id"],
        deferrable=True,
        initially="deferred",
    ),
    sa.ForeignKeyConstraint(
        ["relative_citizen_id", "import_id"],
        ["citizen.citizen_id", "citizen.import_id"],
        deferrable=True,
        initially="deferred",
    ),
)


async def create_tables(engine: aiopg.sa.Engine):
    async with engine.acquire() as conn:
        stmt = sa.dialects.postgresql.CreateEnumType(gender_enum)
        await conn.execute(stmt)

        stmt = sa.schema.CreateSequence(import_seq)
        await conn.execute(stmt)

        for table in [import_table, citizen_table, relative_table]:
            stmt = sa.schema.CreateTable(table)
            await conn.execute(stmt)


async def drop_tables(engine: aiopg.sa.Engine):
    async with engine.acquire() as conn:
        for table in [import_table, citizen_table, relative_table]:
            stmt = f"DROP TABLE IF EXISTS {table.name}"
            await conn.execute(stmt)

        stmt = f"DROP TYPE IF EXISTS {gender_enum.name}"
        await conn.execute(stmt)

        stmt = f"DROP SEQUENCE IF EXISTS {import_seq.name}"
        await conn.execute(stmt)
