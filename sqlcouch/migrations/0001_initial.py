# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'SQLDocModel'
        db.create_table(u'sqlcouch_sqldocmodel', (
            ('doc_id', self.gf('django.db.models.fields.CharField')(max_length=256, primary_key=True)),
            ('rev', self.gf('django.db.models.fields.CharField')(max_length=256, null=True)),
            ('sql_rev', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('doc_type', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('doc_json', self.gf('django.db.models.fields.TextField')()),
            ('synced', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal(u'sqlcouch', ['SQLDocModel'])

        # Adding model 'SQLDocAttachment'
        db.create_table(u'sqlcouch_sqldocattachment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('doc', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['sqlcouch.SQLDocModel'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('content_type', self.gf('django.db.models.fields.CharField')(max_length=256)),
            ('length', self.gf('django.db.models.fields.IntegerField')()),
            ('payload', self.gf('django.db.models.fields.TextField')()),
            ('synced', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal(u'sqlcouch', ['SQLDocAttachment'])

        # Adding unique constraint on 'SQLDocAttachment', fields ['doc', 'name']
        db.create_unique(u'sqlcouch_sqldocattachment', ['doc_id', 'name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'SQLDocAttachment', fields ['doc', 'name']
        db.delete_unique(u'sqlcouch_sqldocattachment', ['doc_id', 'name'])

        # Deleting model 'SQLDocModel'
        db.delete_table(u'sqlcouch_sqldocmodel')

        # Deleting model 'SQLDocAttachment'
        db.delete_table(u'sqlcouch_sqldocattachment')


    models = {
        u'sqlcouch.sqldocattachment': {
            'Meta': {'unique_together': "(('doc', 'name'),)", 'object_name': 'SQLDocAttachment'},
            'content_type': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'doc': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['sqlcouch.SQLDocModel']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'length': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {}),
            'synced': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        },
        u'sqlcouch.sqldocmodel': {
            'Meta': {'object_name': 'SQLDocModel'},
            'doc_id': ('django.db.models.fields.CharField', [], {'max_length': '256', 'primary_key': 'True'}),
            'doc_json': ('django.db.models.fields.TextField', [], {}),
            'doc_type': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'rev': ('django.db.models.fields.CharField', [], {'max_length': '256', 'null': 'True'}),
            'sql_rev': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'synced': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'})
        }
    }

    complete_apps = ['sqlcouch']
