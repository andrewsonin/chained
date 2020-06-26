from inspect import cleandoc

from chained.functions import cleandoc_deco


class ChainedMeta(type):
    """Supplemental metaclass for the needs of this project"""
    __slots__ = ()

    def __new__(mcs, name, bases, attrs):
        # Performs cleandoc of the attribute docstrings
        clean_attrs = {
            k: cleandoc_deco(attr)
            for k, attr
            in attrs.items()
        }

        # Performs cleandoc of the class docstring
        class_doc_str = clean_attrs.get('__doc__', None)
        if class_doc_str is not None:
            clean_attrs['__doc__'] = cleandoc(class_doc_str)

        return super().__new__(mcs, name, bases, clean_attrs)
