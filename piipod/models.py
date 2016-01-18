from piipod import db
from sqlalchemy_utils import ArrowType
import arrow

class Base(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    updated_at = db.Column(ArrowType)
    updated_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(ArrowType, default=arrow.utcnow())
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

    def save(self):
        """Save object"""
        db.session.add(self)
        db.session.commit()
