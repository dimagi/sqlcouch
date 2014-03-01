import base64
from couchdbkit import Database, ResourceNotFound, resource
from couchdbkit.ext.django.schema import Document
from django.db import models, transaction
import json
import uuid
from couchdbkit.exceptions import ResourceConflict


class SQLDocDB(Database):
    def delete_doc(self, doc, **params):
        found = False
        try:
            sqldoc = SQLDocModel.objects.get(doc_id=doc)
        except SQLDocModel.DoesNotExist:
            pass
        else:
            found = True
            sqldoc.delete()
        try:
            return super(SQLDocDB, self).delete_doc(doc)
        except ResourceNotFound:
            if found:
                return {'id': doc, 'ok': True, 'rev': None}
            else:
                raise

    def copy_doc(self, doc, dest=None, headers=None):
        from . import sync
        sync.sync_all()
        return super(SQLDocDB, self).copy_doc(doc, dest, headers)

    def save_doc(self, doc, encode_attachments=True, force_update=False,
                 **params):
        raise NotImplementedError()

    def save_docs(self, docs, use_uuids=True, all_or_nothing=False,
                  **params):
        raise NotImplementedError()

    def delete_docs(self, docs, all_or_nothing=False, empty_on_delete=False,
                    **params):
        raise NotImplementedError()

    def _get(self, docid, **params):
        try:
            doc_model = SQLDocModel.objects.get(doc_id=docid)
        except SQLDocModel.DoesNotExist:
            docid = resource.escape_docid(docid)
            return self.res.get(docid, **params).json_body
        else:
            doc = doc_model.doc
            assert doc['doc_type'] == doc_model.doc_type
            assert doc['_id'] == doc_model.doc_id
            doc['_rev'] = doc_model.sql_rev
            doc['_attachments'] = dict(
                att.format_stub() for att in
                doc_model.sqldocattachment_set.defer('payload')
            )
            return doc

    def open_doc(self, docid, **params):
        # This whole function is copied from Database.open_doc...
        wrapper = None
        if "wrapper" in params:
            wrapper = params.pop("wrapper")
        elif "schema" in params:
            schema = params.pop("schema")
            if not hasattr(schema, "wrap"):
                raise TypeError("invalid schema")
            wrapper = schema.wrap
        # ...except for this line, which is changed
        doc = self._get(docid)
        if wrapper is not None:
            if not callable(wrapper):
                raise TypeError("wrapper isn't a callable")

            return wrapper(doc)

        return doc

    def view(self, *args, **kwargs):
        from . import sync
        sync.sync_all()
        return super(SQLDocDB, self).view(*args, **kwargs)

    bulk_save = save_docs
    bulk_delete = delete_docs
    get = open_doc


class SQLDoc(Document):

    @classmethod
    def get_db(cls):
        db = super(SQLDoc, cls).get_db()
        db.__class__ = SQLDocDB
        return db

    def save(self):
        with transaction.commit_on_success():
            doc_model = self._get_and_lock_sqldoc()
            doc_model.doc_type = self.doc_type
            doc_model.sql_rev = self._new_sql_rev(doc_model.rev)
            doc_model.doc = self.to_json()
            doc_model.save()
        self._rev = doc_model.sql_rev

    def fetch_attachment(self, name):
        try:
            attachment = SQLDocAttachment.objects.get(doc=self._id, name=name)
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
                              .only('doc', 'name')
                              .get(doc=self._id, name=name))
            except SQLDocAttachment.DoesNotExist:
                attachment = SQLDocAttachment(
                    doc=doc_model,
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
        self._rev = doc_model.sql_rev
        if self._attachments is None:
            self._attachments = {}
        self._attachments.__setitem__(*attachment.format_stub())

    def delete_attachment(self, name):
        raise NotImplementedError()

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
            if doc_model.sql_rev != self._rev:
                raise ResourceConflict(
                    '[sqlcouch] (sql)_rev {0} of doc {1} '
                    'does not match the one stored in sql: {2}'
                    .format(self._rev, self._id, doc_model.sql_rev)
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

    def __unicode__(self):
        return ('doc_id={0} rev={1} sql_rev={2} synced={3}'
                .format(self.doc_id, self.rev, self.sql_rev, self.synced))


class SQLDocAttachment(models.Model):
    doc = models.ForeignKey(SQLDocModel)
    name = models.CharField(max_length=256, db_index=True)
    content_type = models.CharField(max_length=256)
    length = models.IntegerField()
    payload = models.TextField()
    synced = models.BooleanField(default=False, db_index=True)

    class Meta:
        unique_together = ('doc', 'name')

    def get_content(self):
        return base64.b64decode(self.payload)

    def set_content(self, content):
        self.payload = base64.b64encode(content)

    content = property(get_content, set_content)

    def format_stub(self):
        return (self.name, {
            'content_type': self.content_type,
            'length': self.length,
            'stub': True,
        })
