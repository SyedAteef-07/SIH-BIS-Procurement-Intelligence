from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload, aliased
from app.database.models import Standard, StandardRelationship


DETAIL_LOAD = (joinedload(Standard.requirements), joinedload(Standard.keywords), joinedload(Standard.certifications), joinedload(Standard.outgoing_relationships).joinedload(StandardRelationship.target))

class StandardRepository:
    def get_related_standards(self, source_codes):
        source = aliased(Standard)
        query = (select(source.standard_code, StandardRelationship.relationship_type, Standard)
                 .join(StandardRelationship, StandardRelationship.target_standard_id == Standard.id)
                 .join(source, StandardRelationship.source_standard_id == source.id)
                 .where(source.standard_code.in_(list(set(source_codes))))
                 .options(*DETAIL_LOAD)
                 .order_by(source.standard_code, Standard.standard_code, StandardRelationship.relationship_type))
        return self.session.execute(query).unique().all() if source_codes else []

    def __init__(self, session):
        self.session = session

    def get_by_code(self, code):
        return self.get_by_codes([code]).get(code)

    def get_by_codes(self, codes):
        codes = list(dict.fromkeys(codes))
        if not codes:
            return {}
        statement = select(Standard).options(*DETAIL_LOAD).where(Standard.standard_code.in_(codes))
        return {s.standard_code: s for s in self.session.scalars(statement).unique()}

    def list_standards(self, search=None, limit=100, offset=0):
        statement = select(Standard).options(*DETAIL_LOAD).order_by(Standard.standard_code)
        if search:
            statement = statement.where(or_(*(column.icontains(search, autoescape=True)
                                              for column in (Standard.standard_code, Standard.title, Standard.scope))))
        return self.session.scalars(statement.limit(limit).offset(offset)).unique().all()
