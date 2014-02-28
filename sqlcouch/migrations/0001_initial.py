# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SQLDocModel'
        db.create_table(u'sqldoc_sqldocmodel', (
            ('doc_id', self.gf('django.db.models.fields.CharField')(max_length=256, primary_key=True)),
            ('rev', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('sql_rev', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('doc_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('doc', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'sqldoc', ['SQLDocModel'])

        # Adding model 'SQLDocAttachment'
        db.create_table(u'sqldoc_sqldocattachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('doc_id', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('length', self.gf('django.db.models.fields.IntegerField')()),
            ('payload', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'sqldoc', ['SQLDocAttachment'])

        # Adding unique constraint on 'SQLDocAttachment', fields ['doc_id', 'name']
        db.create_unique(u'sqldoc_sqldocattachment', ['doc_id', 'name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'SQLDocAttachment', fields ['doc_id', 'name']
        db.delete_unique(u'sqldoc_sqldocattachment', ['doc_id', 'name'])

        # Deleting model 'SQLDocModel'
        db.delete_table(u'sqldoc_sqldocmodel')

        # Deleting model 'SQLDocAttachment'
        db.delete_table(u'sqldoc_sqldocattachment')


    models = {
        u'sqldoc.sqldocattachment': {
            'Meta': {'unique_together': "(('doc_id', 'name'),)", 'object_name': 'SQLDocAttachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'doc_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {})
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
