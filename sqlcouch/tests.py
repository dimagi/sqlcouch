from couchdbkit import ResourceConflict
from couchdbkit.ext.django.schema import StringProperty
from django.test import TestCase
from sqldoc.models import SQLDoc
from sqldoc.sync import sync_all


class MyDoc(SQLDoc):
    name = StringProperty()


class SQLDocTest(TestCase):
    def _test_conflict(self):
        doc = MyDoc(_id='a', name='A')
        yield
        doc.save()
        yield
        doc = MyDoc(_id='a', name='B')
        yield
        with self.assertRaises(ResourceConflict):
            doc.save()
        yield
        doc = MyDoc.get('a')
        yield
        self.assertEqual(doc.name, 'A')
        yield
        doc.name = 'B'
        yield
        doc.save()
        yield
        self.assertEqual(doc.name, 'B')
        yield
        doc = MyDoc.get('a')
        yield
        self.assertEqual(doc.name, 'B')

    def test_conflict(self):
        for _ in self._test_conflict():
            pass

    def test_conflict_with_sync(self):
        for _ in self._test_conflict():
            sync_all()

    def test_attachment(self):
        doc = MyDoc(_id='a', name='A')
        doc.save()
        data = '\x00\x01\x02\xff'
        doc.put_attachment(data, 'data', 'application/octet-stream')
        self.assertEqual(doc.fetch_attachment('data'), data)
        doc.name = 'B'
        doc.save()
        self.assertEqual(MyDoc.get('a').name, 'B')
