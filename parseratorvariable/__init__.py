from collections import OrderedDict
import functools

import numpy
from dedupe.variables.base import DerivedType
from dedupe.variables.string import BaseStringType, StringType, crfEd, affineGap
from probableparsing import RepeatedLabelError

class ParseratorType(BaseStringType) :
    type = None

    _predicate_functions = StringType._predicate_functions
    _index_predicates = StringType._index_predicates
    _index_thresholds = StringType._index_thresholds

    def __len__(self) :
        return self.expanded_size

    def __init__(self, definition) :
        super(ParseratorType, self).__init__(definition)

        if definition.get('crf', False) == True :
            self._string_comparison = crfEd
        else :
            self._string_comparison = affineGap

        self._definition = definition

        self.variable_types, self.variable_parts = comparisons(self.components)

        self.n_type_indicators = len(self.variable_types) - 1
        self.n_parts = len(self.variable_parts)

        # missing? + ambiguous? + same_type? + len(indicator) + ...
        # + full_string
        self.expanded_size = (1 + 1 + 1 + self.n_type_indicators 
                              + 2 * self.n_parts + 1)

        fields = self.fields(definition['field'])
        
        self.higher_vars = [DerivedType({'name' : variable,
                                         'type' : field_type})
                            for variable, field_type in fields]

        self.log_file = definition.get('log file', None)

    def __getstate__(self) :
        return self._definition.copy()

    def __setstate__(self, d) :
        self.__init__(d)


    def comparator(self, field_1, field_2) :
        distances = numpy.zeros(self.expanded_size)
        i = 0

        if not (field_1 and field_2) :
            return distances
        
        distances[i] = 1
        i += 1

        try :
            parsed_variable_1, variable_type_1 = self.tagger(field_1) 
            parsed_variable_2, variable_type_2  = self.tagger(field_2)
        except RepeatedLabelError as e:
            if self.log_file :
                import csv
                with open(self.log_file, 'a') as f :
                    writer = csv.writer(f)
                    writer.writerow([e.original_string.encode('utf8')])
            distances[i:3] = [1, 0]
            distances[-1] = self.compareString(field_1, field_2)
            return distances

        if 'Ambiguous' in (variable_type_1, variable_type_2) :
            distances[i:3] = [1, 0]
            distances[-1] = self.compareString(field_1, field_2)
            return distances
        elif variable_type_1 != variable_type_2 :
            distances[i:3] = [0, 0]
            distances[-1] = self.compareString(field_1, field_2)
            return distances
        elif variable_type_1 == variable_type_2 : 
            distances[i:3] = [0, 1]

        i += 2

        variable_type = self.variable_types[variable_type_1]

        distances[i:i+self.n_type_indicators] = variable_type['indicator']
        i += self.n_type_indicators

        i += variable_type['offset']
        for j, dist in enumerate(variable_type['compare'](parsed_variable_1, 
                                                          parsed_variable_2), 
                                 i) :
            distances[j] = dist

        unobserved_parts = numpy.isnan(distances[i:j+1])
        distances[i:j+1][unobserved_parts] = 0
        unobserved_parts = (~unobserved_parts).astype(int)
        distances[(i + self.n_parts):(j + 1 + self.n_parts)] = unobserved_parts

        return distances

    def fields(self, field) :
        fields = [('%s: Not Missing' % field, 'Dummy'),
                  ('ambiguous', 'Dummy'),
                  ('same name type?', 'Dummy')]

        fields += [(k.lower(), 'Dummy')
                   for k in list(self.variable_types.keys())[1:]] 

        fields += [(part, 'Derived') 
                   for part in self.variable_parts]

        fields += [('%s: Not Missing' % (part,), 
                    'Not Missing') 
                   for part in self.variable_parts]

        fields += [('full string', 'String')]

        return fields

    def compareFields(self, parts, field_1, field_2) :
        joinParts = functools.partial(consolidate, components=parts)    
        for part_1, part_2 in zip(*map(joinParts, [field_1, field_2])) :
            yield self.compareString(part_1, part_2)

    def comparePermutable(self, tags_1, tags_2, field_1, field_2) :

        section_1A = tuple(consolidate(field_1, tags_1))
        section_1B = tuple(consolidate(field_1, tags_2))
        whole_2 = tuple(consolidate(field_2, tags_1 + tags_2))

        straight_distances = [self.compareString(part_1, part_2)
                              for part_1, part_2 
                              in zip(section_1A + section_1B, whole_2)]

        permuted_distances = [self.compareString(part_1, part_2)
                               for part_1, part_2 
                               in zip(section_1B + section_1A, whole_2)]

        if numpy.nansum(straight_distances) <= numpy.nansum(permuted_distances) :
            return straight_distances
        else :
            return permuted_distances

    def compareString(self, string_1, string_2) :
        if string_1 and string_2 :
            return self._string_comparison(string_1, string_2)
        else :
            return numpy.nan


def comparisons(components) :
    variable_types = OrderedDict()
    tag_names = []
    offset = 0

    n_components = len(components)
    
    for i, component in enumerate(components) :
        key, compare_func, parts = component[0], component[1], component[2:]

        args = []
        for part in parts :
            names, tags = list(zip(*part))
            tag_names.extend(names)
            args.append(tags)

        comparison = {'compare' : functools.partial(compare_func, *args),
                      'indicator' : indicatorVector(i, n_components),
                      'offset' : offset }

        variable_types[key] = comparison

        offset = len(tag_names)
    
    return variable_types, tag_names




def consolidate(d, components) :
    for component in components :
        available_component = [part for part in component if part in d]
        # Sometimes we want to return non strings so we have to avoid
        # join
        if len(available_component) == 1 :
            yield d[available_component[0]]
        else :
            yield ' '.join(d[part] for part in available_component)

    
def indicatorVector(value, n_categories) :
    response = numpy.zeros(n_categories-1)
    if value :
        response[value - 1] = 1
    return response
