from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload
from app.database.models import Standard


class StandardRepository:
    def __init__(self, session):
        self.session = session

    def get_by_code(self, code):
        return self.get_by_codes([code]).get(code)

    def get_by_codes(self, codes):
        codes = list(dict.fromkeys(codes))
        if not codes:
            return {}
        statement = select(Standard).options(joinedload(Standard.keywords)).where(Standard.standard_code.in_(codes))
        return {s.standard_code: s for s in self.session.scalars(statement).unique()}

    def list_standards(self, search=None, limit=100, offset=0):
        statement = select(Standard).options(joinedload(Standard.keywords)).order_by(Standard.standard_code)
        if search:
            statement = statement.where(or_(*(column.icontains(search, autoescape=True)
                                              for column in (Standard.standard_code, Standard.title, Standard.scope))))
        return self.session.scalars(statement.limit(limit).offset(offset)).unique().all()
