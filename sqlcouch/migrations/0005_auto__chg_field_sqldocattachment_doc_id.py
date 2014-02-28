# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'SQLDocAttachment.doc_id'
        db.alter_column(u'sqldoc_sqldocattachment', 'doc_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sqldoc.SQLDocModel'], db_column='doc_id'))


    def backwards(self, orm):
        
        # Changing field 'SQLDocAttachment.doc_id'
        db.alter_column(u'sqldoc_sqldocattachment', 'doc_id', self.gf('django.db.models.fields.CharField')(max_length=256))


    models = {
        u'sqldoc.sqldocattachment': {
            'Meta': {'unique_together': "(('doc_id', 'name'),)", 'object_name': 'SQLDocAttachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'doc_id': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sqldoc.SQLDocModel']", 'db_column': "'doc_id'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'synced': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        u'sqldoc.sqldocmodel': {
            'Meta': {'object_name': 'SQLDocModel'},
            'doc_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'primary_key': 'True'}),
            'doc_json': ('django.db.models.fields.TextField', [], {}),
            'doc_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'rev': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'sql_rev': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'synced': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        }
    }

    complete_apps = ['sqldoc']
