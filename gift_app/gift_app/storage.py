import logging
from itertools import groupby
from operator import itemgetter
from typing import List, Optional

import asyncpg
import asyncpgsa
import sqlalchemy as sa

from .config import Config
from .errors import InvalidUsage
from .models import Citizen, Gender, ImportMessage


class Storage:
    def __init__(self, config: Config, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._pool = None

    async def initialize(self):
        DSN = "postgresql://{username}:{password}@{host}:{port}/{db_name}"
        pool = await asyncpgsa.create_pool(
            dsn=DSN.format(
                username=self.config.db.username,
                password=self.config.db.password,
                host=self.config.db.host,
                port=self.config.db.port,
                db_name=self.config.db.name,
            )
        )
        self._pool = pool
        return self

    @property
    def pool(self) -> asyncpg.pool.Pool:
        if not self._pool:
            raise RuntimeError("Storage is not initialized")
        return self._pool

    async def import_citizens(self, citizens: List[Citizen]) -> int:
        async with self.pool.transaction() as conn:  # type: asyncpg.connection.Connection
            import_id = await self._next_import_id(conn)
            await self._create_import(conn, import_id)
            citizen_insert_args = []
            relative_insert_args = []
            for citizen in citizens:
                citizen_insert_args.append(
                    dict(
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
                    relative_insert_args.append(
                        dict(
                            import_id=import_id,
                            citizen_id=citizen.citizen_id,
                            relative_citizen_id=relative,
                        )
                    )
            await conn.fetchrow(citizen_table.insert().values(citizen_insert_args))
            await conn.fetchrow(relative_table.insert().values(relative_insert_args))
            return import_id

    async def retrieve_citizen(
        self, import_id: int, citizen_id: int
    ) -> Citizen:
        async with self.pool.transaction() as conn:  # type: asyncpg.connection.Connection
            citizen = await self._retrieve_citizen(conn, import_id, citizen_id)
            if not citizen:
                raise InvalidUsage.not_found(
                    f"Житель #{citizen_id} из набора #{import_id} не найден"
                )
            return citizen

    async def list_citizens(
        self, import_id: int
    ) -> List[Citizen]:
        async with self.pool.transaction() as conn:  # type: asyncpg.connection.Connection
            citizens = await self._list_citizens(conn, import_id)
            return citizens

    async def update_citizen(
        self, import_id: int, citizen_id: int, citizen_update: dict
    ) -> Citizen:
        async with self.pool.transaction() as conn:  # type: asyncpg.connection.Connection
            if "relatives" in citizen_update:
                await self._update_citizen_relatives(
                    conn, import_id, citizen_id, citizen_update.pop("relatives")
                )
            if citizen_update:
                stmt = citizen_table.update().where(citizen_table.c.citizen_id == citizen_id).values(**citizen_update)
                await conn.fetchrow(stmt)
            new_citizen = await self._retrieve_citizen(conn, import_id, citizen_id)
            assert new_citizen
            return new_citizen

    async def _update_citizen_relatives(
        self,
        conn: asyncpg.connection.Connection,
        import_id: int,
        citizen_id: int,
        new_relatives: List[int],
    ) -> List[int]:
        new_relatives_set = set(new_relatives)
        old_relatives = set(
            await self._retrieve_citizen_relatives_ids(conn, import_id, citizen_id)
        )
        to_delete = old_relatives - new_relatives_set
        to_add = new_relatives_set - old_relatives
        for relative in to_delete:
            await conn.fetchrow(
                relative_table.delete()
                .where(relative_table.c.import_id == import_id)
                .where(relative_table.c.citizen_id == citizen_id)
                .where(relative_table.c.relative_citizen_id == relative)
            )
            await conn.fetchrow(
                relative_table.delete()
                .where(relative_table.c.import_id == import_id)
                .where(relative_table.c.citizen_id == relative)
                .where(relative_table.c.relative_citizen_id == citizen_id)
            )
        for relative in to_add:
            if not await self._check_citizen_exists(conn, import_id, relative):
                raise InvalidUsage.bad_request(f'Родственник #{relative} не существует в наборе #{import_id}.')
            await conn.fetchrow(
                relative_table.insert().values(
                    import_id=import_id,
                    citizen_id=citizen_id,
                    relative_citizen_id=relative,
                )
            )
            await conn.fetchrow(
                relative_table.insert().values(
                    import_id=import_id,
                    citizen_id=relative,
                    relative_citizen_id=citizen_id,
                )
            )
        saved_relatives = await self._retrieve_citizen_relatives_ids(
            conn, import_id, citizen_id
        )
        return saved_relatives

    async def _retrieve_citizen_relatives_ids(
        self, conn: asyncpg.connection.Connection, import_id: int, citizen_id: int
    ) -> List[int]:
        r = await conn.fetch(
            relative_table.select()
            .where(relative_table.c.import_id == import_id)
            .where(relative_table.c.citizen_id == citizen_id)
        )
        relative_ids = []
        for row in r:
            relative_ids.append(row["relative_citizen_id"])
        return relative_ids

    async def next_import_id(self) -> int:
        async with self.pool.transaction() as conn:  # type: asyncpg.connection.Connection
            return await self._next_import_id(conn)

    async def _check_citizen_exists(
        self, conn: asyncpg.connection.Connection, import_id: int, citizen_id: int
    ) -> bool:
        val = await conn.fetchval(
            citizen_table.select()
            .where(citizen_table.c.citizen_id == citizen_id)
            .where(citizen_table.c.import_id == import_id)
            .limit(1)
        )
        return bool(val)

    async def _retrieve_citizen(
        self, conn: asyncpg.connection.Connection, import_id: int, citizen_id: int
    ) -> Optional[Citizen]:
        row = await conn.fetchrow(
            citizen_table.select()
            .where(citizen_table.c.citizen_id == citizen_id)
            .where(citizen_table.c.import_id == import_id)
            .limit(1)
        )
        if not row:
            return None
        citizen = _citizen_from_row(row)
        relatives = await self._retrieve_citizen_relatives_ids(conn, import_id, citizen_id)
        citizen.relatives = relatives
        return citizen

    async def _list_citizens(
        self, conn: asyncpg.connection.Connection, import_id: int
    ) -> List[Citizen]:
        citizens_rows = await conn.fetch(
            citizen_table.select()
            .where(citizen_table.c.import_id == import_id)
            .order_by(citizen_table.c.citizen_id)
        )
        relatives_rows = await conn.fetch(
            relative_table.select()
            .where(relative_table.c.import_id == import_id)
        )
        relatives_map = {
            citizen_id: list(map(itemgetter("citizen_id"), relatives_it))
            for citizen_id, relatives_it in
            groupby(relatives_rows, key=itemgetter("relative_citizen_id"))
        }
        citizens = []
        for citizen_row in citizens_rows:
            citizen = _citizen_from_row(citizen_row)
            citizen.relatives = relatives_map.get(citizen.citizen_id, [])
            citizens.append(citizen)
        return citizens

    async def _retrieve_many_citizens(
        self, conn, import_id: int, citizen_ids: List[int]
    ) -> List[Citizen]:
        rows = await conn.fetch(
            citizen_table.select()
            .where(citizen_table.c.import_id == import_id)
            .where(citizen_table.c.citizen_id.in_(citizen_ids))
        )
        if len(rows) != len(citizen_ids):
            # Кто-то из списка не был найден в базе данных.
            assert len(rows) < len(citizen_ids)
            ids = set(citizen_ids)
            for row in rows:
                ids.remove(row["id"])
            raise InvalidUsage.not_found(
                f"Некоторые жители не были найдены: {''.join(str(x) for x in ids)}"
            )
        citizens = []
        for row in rows:
            citizen = _citizen_from_row(row)
            citizens.append(citizen)
        return citizens

    async def _import_exists(
        self, conn: asyncpg.connection.Connection, import_id: int
    ) -> bool:
        r = await conn.fetchval(
            import_table.select().where(import_table.c.import_id == import_id).limit(1)
        )
        return bool(r)

    async def _create_import(
        self, conn: asyncpg.connection.Connection, import_id: int
    ) -> int:
        r = await conn.fetchrow(import_table.insert().values(import_id=import_id))
        return bool(r)

    async def _next_import_id(self, conn: asyncpg.connection.Connection) -> int:
        t = await conn.fetchval(sa.select([import_seq.next_value()]))
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


async def create_tables(conn: asyncpg.connection.Connection):
    stmt = sa.dialects.postgresql.CreateEnumType(gender_enum)
    await conn.execute(stmt)

    stmt = sa.schema.CreateSequence(import_seq)
    await conn.execute(stmt)

    for table in [import_table, citizen_table, relative_table]:
        stmt = sa.schema.CreateTable(table)
        await conn.execute(stmt)


async def drop_tables(conn: asyncpg.connection.Connection):
    for table in [import_table, citizen_table, relative_table]:
        stmt = f"DROP TABLE IF EXISTS {table.name}"
        await conn.execute(stmt)

    stmt = f"DROP TYPE IF EXISTS {gender_enum.name}"
    await conn.execute(stmt)

    stmt = f"DROP SEQUENCE IF EXISTS {import_seq.name}"
    await conn.execute(stmt)

def _citizen_from_row(row) -> Citizen:
    citizen = Citizen(
        citizen_id=row["citizen_id"],
        town=row["town"],
        street=row["street"],
        building=row["building"],
        apartment=row["apartment"],
        name=row["name"],
        birth_date=row["birth_date"],
        gender=Gender.male if row["gender"] == "male" else Gender.female,
    )
    return citizen
