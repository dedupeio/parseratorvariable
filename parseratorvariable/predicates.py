from probableparsing import RepeatedLabelError
from dedupe import predicates

class Partial(object):
    cached_field = None
    cached_results = None

    @classmethod
    def tag(cls, field):
        if field == cls.cached_field:
            return cls.cached_results

        cls.cached_field = field
        try:
            cls.cached_results, _ = cls.tagger(field)
        except RepeatedLabelError:
            cls.cached_results = {}

        return cls.cached_results

class PartialIndex(Partial):
    def __init__(self, *args, **kwargs):
        self.part = kwargs.pop('part')
        super(PartialIndex, self).__init__(*args, **kwargs)
        self.__name__ = '(%s, %s, %s)' % (self.threshold, self.field, self.part)
    
    def preprocess(self, doc):
        tags = self.tag(doc)
        part = tags.get(self.part, '')
        return super(PartialIndex, self).preprocess(part)

class PLCPredicate(PartialIndex, predicates.LevenshteinCanopyPredicate):
    type = "PartialIndexLevenshteinCanopyPredicate"

class PLSPredicate(PartialIndex, predicates.LevenshteinSearchPredicate):
    type = "PartialIndexLevenshteinSearchPredicate"

class PTNCPredicate(PartialIndex, predicates.TfidfNGramCanopyPredicate):
    type = "PartialIndexTfidfNGramCanopyPredicate"

class PTNSPredicate(PartialIndex, predicates.TfidfNGramSearchPredicate):
    type = "PartialIndexTfidfNGramSearchPredicate"

class PTTCPredicate(PartialIndex, predicates.TfidfTextCanopyPredicate):
    type = "PartialIndexTfidfTextCanopyPredicate"

class PTTSPredicate(PartialIndex, predicates.TfidfTextSearchPredicate):
    type = "PartialIndexTfidfTextSearchPredicate"

class PartialString(Partial, predicates.StringPredicate):
    type = 'PartialPredicate'
    
    def __init__(self, func, field, part):
        self.func = func
        self.__name__ = "(%s, %s, %s)" % (func.__name__, field, part)
        self.field = field
        self.part = part

    def __call__(self, record, **kwargs) :
        column = record[self.field]
        if not column :
            return ()

        tags = self.tag(column)
        part = tags.get(self.part)
        if not part:
            return ()

        return super(PartialString, self).__call__({self.field: part})
