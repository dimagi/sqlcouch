import uuid
from couchdbkit import ResourceConflict
from couchdbkit.ext.django.schema import StringProperty
from django.test import TestCase
import time
from sqlcouch.models import SQLDoc, SQLDocModel
from sqlcouch.sync import sync_all


class MyDoc(SQLDoc):
    name = StringProperty()


class SQLDocTest(TestCase):

    def _get_id(self):
        return uuid.uuid4().hex

    @property
    def _test_conflict(self):
        id = self._get_id()
        doc = MyDoc(_id=id, name='A')
        yield
        doc.save()
        yield
        doc = MyDoc(_id=id, name='B')
        yield
        with self.assertRaises(ResourceConflict):
            doc.save()
        yield
        doc = MyDoc.get(id)
        yield
        self.assertEqual(doc.name, 'A')
        yield
        doc.name = 'B'
        yield
        doc.save()
        yield
        self.assertEqual(doc.name, 'B')
        yield
        doc = MyDoc.get(id)
        yield
        self.assertEqual(doc.name, 'B')

    def test_conflict(self):
        for _ in self._test_conflict:
            pass

    def test_conflict_with_sync(self):
        for _ in self._test_conflict:
            sync_all()

    def test_attachment(self):
        id = self._get_id()
        doc = MyDoc(_id=id, name='A')
        doc.save()
        data = '\x00\x01\x02\xff'
        doc.put_attachment(data, 'data', 'application/octet-stream')
        self.assertEqual(doc.fetch_attachment('data'), data)
        doc.name = 'B'
        doc.save()
        self.assertEqual(MyDoc.get(id).name, 'B')

    def test_copy_delete(self):
        doc_id = self._get_id()
        doc = MyDoc(_id=doc_id)
        doc.save()
        doc_id2 = MyDoc.get_db().copy_doc(doc_id)['id']
        doc2 = MyDoc.get(doc_id2)
        doc2.save()
        MyDoc.get_db().delete_doc(doc_id)

        doc = MyDoc(_id=doc_id)
        doc.save()
        from . import sync
        sync.sync_all()
        doc_id2 = MyDoc.get_db().copy_doc(doc_id)['id']
        doc2 = MyDoc.get(doc_id2)
        doc2.save()
        MyDoc.get_db().delete_doc(doc_id)
