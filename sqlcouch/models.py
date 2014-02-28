import base64
from couchdbkit import Database
from couchdbkit.ext.django.schema import Document
from django.conf import settings
from django.db import models, transaction
import json
import uuid
from couchdbkit.exceptions import ResourceConflict


class StiltedDB(Database):
    def delete_doc(self, doc, **params):
        raise NotImplementedError()


class SQLDoc(Document):
    _sql_rev = None

    @classmethod
    def get_db(cls):
        from .import sync
        sync.sync_all()
        db = super(SQLDoc, cls).get_db()
        db.__class__ = StiltedDB
        return db

    def delete(self):
        raise NotImplementedError()

    @classmethod
    def get(cls, docid):
        try:
            doc_model = SQLDocModel.objects.get(doc_id=docid)
        except SQLDocModel.DoesNotExist:
            return super(SQLDoc, cls).get(docid)
        else:
            self = cls.wrap(doc_model.doc)
            assert self.doc_type == doc_model.doc_type
            assert self._id == doc_model.doc_id
            self._sql_rev = doc_model.sql_rev
            return self

    def save(self):
        with transaction.commit_on_success():
            doc_model = self._get_and_lock_sqldoc()
            doc_model.doc_type = self.doc_type
            doc_model.sql_rev = self._new_sql_rev(doc_model.rev)
            doc_model.doc = self.to_json()
            doc_model.save()
        self._sql_rev = doc_model.sql_rev
        if settings.UNIT_TESTING:
            from .import sync
            sync.sync_all()

    def fetch_attachment(self, name):
        try:
            attachment = SQLDocAttachment.objects.get(doc_id=self._id, name=name)
        except SQLDocAttachment.DoesNotExist:
            return super(SQLDoc, self).fetch_attachment(name)
        else:
            content = attachment.content
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content

    def put_attachment(self, content, name=None, content_type=None,
                       content_length=None):
        with transaction.commit_on_success():
            doc_model = self._get_and_lock_sqldoc()
            try:
                attachment = (SQLDocAttachment.objects.select_for_update()
                              .only('doc_id', 'name')
                              .get(doc_id=self._id, name=name))
            except SQLDocAttachment.DoesNotExist:
                attachment = SQLDocAttachment(
                    doc_id=doc_model,
                    name=name
                )
            if hasattr(content, 'read'):
                content = content.read()
            if isinstance(content, unicode):
                content = content.encode('utf-8')
            attachment.content = content
            attachment.content_type = content_type
            attachment.length = content_length or len(content)
            doc_model.sql_rev = self._new_sql_rev(doc_model.rev)
            attachment.save()
            doc_model.save()
        self._sql_rev = doc_model.sql_rev
        if settings.UNIT_TESTING:
            from .import sync
            sync.sync_all()

    def _get_and_lock_sqldoc(self):
        """This should be done inside a transaction"""
        if not self._id:
            self._id = self.get_db().server.next_uuid()
        try:
            doc_model = (SQLDocModel.objects.select_for_update()
                         .only('rev', 'sql_rev', 'doc_id').get(pk=self._id))
        except SQLDocModel.DoesNotExist:
            doc_model = SQLDocModel(doc_id=self._id, rev=self._rev)
        else:
            if doc_model.sql_rev != self._sql_rev:
                print doc_model.sql_rev, self._sql_rev
                raise ResourceConflict(
                    '[sqldoc] _sql_rev {0} of doc {1} '
                    'does not match the one stored in sql: {2}'
                    .format(self._sql_rev, self._id, doc_model.sql_rev)
                )
        return doc_model

    def _new_sql_rev(self, rev):
        return (rev or '') + '-' + uuid.uuid4().hex


class SQLDocModel(models.Model):
    doc_id = models.CharField(max_length=256, primary_key=True)
    rev = models.CharField(max_length=256, null=True)
    # docs stored in postgres will need their own rev scheme
    # that mimics couchdb's, because docs may be saved a number of times
    # in postgres before it's synced to couchdb
    # if couchdb is up to date, sql_rev and rev will be equal
    sql_rev = models.CharField(max_length=256)
    doc_type = models.CharField(max_length=20)
    doc_json = models.TextField()
    synced = models.BooleanField(default=False, db_index=True)

    def get_doc(self):
        return json.loads(self.doc_json)

    def set_doc(self, doc):
        self.doc_json = json.dumps(doc)

    doc = property(get_doc, set_doc)


class SQLDocAttachment(models.Model):
    doc_id = models.ForeignKey(SQLDocModel, db_column='doc_id')
    name = models.CharField(max_length=256, db_index=True)
    content_type = models.CharField(max_length=256)
    length = models.IntegerField()
    payload = models.TextField()
    synced = models.BooleanField(default=False, db_index=True)

    class Meta:
        unique_together = ('doc_id', 'name')

    def get_content(self):
        return base64.b64decode(self.payload)

    def set_content(self, content):
        self.payload = base64.b64encode(content)

    content = property(get_content, set_content)
