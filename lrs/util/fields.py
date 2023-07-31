import uuid

from django.db.models import CharField
from django.utils.encoding import force_unicode


class CustomUUIDField(CharField):
    """ CustomUUIDField

    By default, uses UUID version 4 (randomly generated UUID).

    The field support all uuid versions which are natively supported by the uuid python module, except version 2.
    For more information see: https://docs.python.org/3/library/uuid.html
    """

    DEFAULT_MAX_LENGTH = 36

    def __init__(self, verbose_name=None, name=None, auto=True, version=4, node=None, clock_seq=None, namespace=None,
                 uuid_name=None, *args, **kwargs):

        kwargs.setdefault('max_length', self.DEFAULT_MAX_LENGTH)
        if auto:
            self.empty_strings_allowed = False
            kwargs['blank'] = True
            kwargs.setdefault('editable', False)
        self.auto = auto
        self.version = version
        self.node = node
        self.clock_seq = clock_seq
        self.namespace = namespace
        self.uuid_name = uuid_name or name
        super(CustomUUIDField, self).__init__(verbose_name=verbose_name, *args, **kwargs)

    def create_uuid(self):
        if not self.version or self.version == 4:
            return uuid.uuid4()
        elif self.version == 1:
            return uuid.uuid1(self.node, self.clock_seq)
        elif self.version == 2:
            raise ValueError("UUID version 2 is not supported.")
        elif self.version == 3:
            return uuid.uuid3(self.namespace, self.name)
        elif self.version == 5:
            return uuid.uuid5(self.namespace, self.name)
        else:
            raise ValueError("UUID version %s is not valid." % self.version)

    def pre_save(self, model_instance, add):
        value = super(CustomUUIDField, self).pre_save(model_instance, add)
        if self.auto and add and value is None:
            value = force_unicode(self.create_uuid())
            setattr(model_instance, self.attname, value)
            return value
        else:
            if self.auto and not value:
                value = force_unicode(self.create_uuid())
                setattr(model_instance, self.attname, value)
        return value

    def formfield(self, **kwargs):
        if self.auto:
            return None
        return super(CustomUUIDField, self).formfield(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(CustomUUIDField, self).deconstruct()
        if kwargs.get('max_length', None) == self.DEFAULT_MAX_LENGTH:
            del kwargs['max_length']
        if self.auto is not True:
            kwargs['auto'] = self.auto
        if self.version != 4:
            kwargs['version'] = self.version
        if self.node is not None:
            kwargs['node'] = self.node
        if self.clock_seq is not None:
            kwargs['clock_seq'] = self.clock_seq
        if self.namespace is not None:
            kwargs['namespace'] = self.namespace
        if self.uuid_name is not None:
            kwargs['uuid_name'] = self.name
        return name, path, args, kwargs
