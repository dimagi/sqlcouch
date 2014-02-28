import sys
from django.db.models import Q
from sqldoc.exceptions import NoMoreData
from sqldoc.models import SQLDocModel, SQLDocAttachment
from collections import defaultdict
import json
from dimagi.utils.couch.database import get_db


def assert_equal(one, *args):
    if [arg for arg in args if arg != one]:
        raise AssertionError('Not all equal: {0}'.format((one,) + args))


def sync_all(limit=10, force_save=False, stdout=sys.stdout):
    while True:
        try:
            batch_sync(limit=limit, force_save=force_save, stdout=stdout)
        except NoMoreData:
            break


def batch_sync(limit=10, force_save=False, stdout=sys.stdout):
    ids = SQLDocModel.objects.filter(
        Q(synced=False) | Q(sqldocattachment__synced=False)
    )[:limit].values_list('doc_id', flat=True)
    sqldocs = SQLDocModel.objects.select_for_update().filter(doc_id__in=ids)
    ids = [s.doc_id for s in sqldocs]
    if not ids:
        raise NoMoreData()

    sqlatts = (SQLDocAttachment.objects.select_for_update()
               .filter(doc_id__in=ids)).all()

    sql_attachments = defaultdict(list)
    for sqlatt in sqlatts:
        sql_attachments[sqlatt.doc_id.doc_id].append(sqlatt)

    db = get_db()
    couch_results = db.all_docs(keys=ids, include_docs=True).all()
    new_docs = []
    for sqldoc, result in zip(sqldocs, couch_results):
        sqldoc_json = sqldoc.doc
        sqldoc_json.pop('_attachments', None)
        couch_json = result.get('doc')
        if couch_json:
            if not force_save:
                assert_equal(
                    couch_json.get('_rev'),
                    sqldoc.rev,
                )
            sqldoc_json.pop('_rev', None)
            couch_json.update(sqldoc_json)
        else:
            couch_json = sqldoc_json
        if '_attachments' not in couch_json:
            couch_json['_attachments'] = {}
        for sqlatt in sql_attachments[sqldoc.doc_id]:
            assert_equal(sqlatt.doc_id.doc_id, sqldoc.doc_id,
                         couch_json['_id'])
            couch_json['_attachments'][sqlatt.name] = {
                'content_type': sqlatt.content_type,
                # payload is base64 encoded already
                'data': sqlatt.payload,
            }
        new_docs.append(couch_json)
    save_results = db.bulk_save(new_docs, all_or_nothing=True)
    for sqldoc, result in zip(sqldocs, save_results):
        assert sqldoc.doc_id == result['id']
        rev = result['rev']
        if rev:
            sqldoc.rev = rev
            for sqlatt in sql_attachments[sqldoc.doc_id]:
                sqlatt.synced = True
                sqlatt.save()
            sqldoc.synced = True
            sqldoc.save()
            stdout.write('Saved {0}'.format(sqldoc.doc_id))
        else:
            stdout.write('Error saving: {0}'
                         .format(json.dumps(result)))
