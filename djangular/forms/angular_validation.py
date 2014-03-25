# -*- coding: utf-8 -*-
import types
from django.conf import settings
from django.utils.importlib import import_module
from django.utils.html import format_html
from djangular.forms.angular_base import NgFormBaseMixin

VALIDATION_MAPPING_MODULE = import_module(getattr(settings, 'DJANGULAR_VALIDATION_MAPPING_MODULE', 'djangular.forms.patched_fields'))


class NgFormValidationMixin(NgFormBaseMixin):
    """
    Add this NgFormValidationMixin to every class derived from forms.Form, which shall be
    auto validated using the Angular's validation mechanism.
    """
    def __init__(self, *args, **kwargs):
        super(NgFormValidationMixin, self).__init__(*args, **kwargs)
        for name, field in self.fields.items():
            # add ng-model to each model field
            ng_model = self.add_prefix(name)
            field.widget.attrs.setdefault('ng-model', ng_model)
            setattr(field, 'ng_field_name', '{0}.{1}'.format(self.name(), ng_model))
            # each field type may have different errors and additional AngularJS specific attributes
            ng_errors_function = '{0}_angular_errors'.format(field.__class__.__name__)
            try:
                ng_errors_function = getattr(VALIDATION_MAPPING_MODULE, ng_errors_function)
                ng_potential_errors = types.MethodType(ng_errors_function, field)()
            except (TypeError, AttributeError):
                ng_errors_function = getattr(VALIDATION_MAPPING_MODULE, 'Default_angular_errors')
                ng_potential_errors = types.MethodType(ng_errors_function, field)()
            extra_list_item = format_html('<li ng-show="{0}.$valid" class="valid"></li>', field.ng_field_name)
            ng_error_class = type('NgErrorList', (self.NgErrorClass,),
                {'identifier': field.ng_field_name, 'property': '$pristine', 'extra_list_item': extra_list_item})
            setattr(field, 'ng_potential_errors', ng_error_class(ng_potential_errors))

    def _post_clean(self):
        super(NgFormValidationMixin, self)._post_clean()
        # transfer field errors generated by the server into a special error list managed by Angular
        for name, error_list in self._errors.items():
            try:
                field = self.fields[name]
                ng_error_class = type('NgErrorList', (self.NgErrorClass,),
                    {'identifier': field.ng_field_name, 'property': '$dirty'})
                setattr(field, 'ng_detected_errors', ng_error_class(('$pristine', e) for e in error_list))
                setattr(error_list, '_ng_non_field_errors', False)
            except KeyError:
                # presumably this is a non-field error
                setattr(error_list, '_ng_non_field_errors', True)
