# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'SQLDocAttachment.synced'
        db.add_column(u'sqldoc_sqldocattachment', 'synced', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'SQLDocAttachment.synced'
        db.delete_column(u'sqldoc_sqldocattachment', 'synced')


    models = {
        u'sqldoc.sqldocattachment': {
            'Meta': {'unique_together': "(('doc_id', 'name'),)", 'object_name': 'SQLDocAttachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'doc_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'synced': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        u'sqldoc.sqldocmodel': {
            'Meta': {'object_name': 'SQLDocModel'},
            'doc': ('django.db.models.fields.TextField', [], {}),
            'doc_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'primary_key': 'True'}),
            'doc_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'rev': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'sql_rev': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        }
    }

    complete_apps = ['sqldoc']
