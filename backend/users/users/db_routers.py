import random

class ReadReplicaRouter:
    def db_for_read(self, model, **hints):
        # All reads go to the replica
        return 'replica'

    def db_for_write(self, model, **hints):
        # All writes go to the main DB
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between any DBs
        return True

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        # Only apply migrations to the default DB
        return db == 'default'
