# -*- coding: utf-8 -*-
import json

from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import modelform_factory
from django.http import HttpResponse
from django.views.generic import FormView


class NgCRUDView(FormView):
    """
    Basic view to support default angular $resource CRUD actions on server side
    Required attributes: model_class

    Requires two entries in urlconf, a general one without object id's and an object-specific one (with id)
    Example:
        url(r'url$', NgCRUDView.as_view()),
        url(r'url/(?P<pk>\d+)$', NgCRUDView.as_view()),  # parameter name must be 'pk'
    """
    model_class = None
    content_type = 'application/json'

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to call appropriate methods:
        * $query - ng_query
        * $get - ng_get
        * $save - ng_save
        * $delete and $remove - ng_delete
        """
        if request.method == 'GET':
            if 'pk' in self.kwargs:
                return self.ng_get(request, *args, **kwargs)
            return self.ng_query(request, *args, **kwargs)
        elif request.method == 'POST':
            return self.ng_save(request, *args, **kwargs)
        elif request.method == 'DELETE':
            return self.ng_delete(request, *args, **kwargs)
        raise ValueError('This view can not handle method %s' % request.method)

    def get_form_class(self):
        """
        Build ModelForm from model_class
        """
        return modelform_factory(self.model_class)

    def get_model_fields(self):
        """
        Returns a list of field names to include in JSON response
        By default includes all model's fields, except ManyToMany relations

        model_to_dict doesn't include fields with editable=False, such as DatetimeField(auto_now_add=True)
        Hence manual approach is required
        """
        fields = [field.name for field in self.model_class._meta.fields]
        # pk is preferable to id
        fields.remove('id')
        fields.append('pk')
        return fields

    def build_model_dict(self, obj):
        """
        Using field names from get_model_fields() builds a dictionary with fieldnames and corresponding values
        """
        return {field: getattr(obj, field) for field in self.get_model_fields()}

    def build_json_response(self, data):
        return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), self.content_type)

    def get_form_kwargs(self):
        """
        Modify form kwargs
        Add instance when pk is present
        fix data
        """
        kwargs = super(NgCRUDView, self).get_form_kwargs()
        # Since angular sends data in JSON rather than as POST parameters, the default data (request.POST)
        # is replaced with request.body that contains JSON encoded data
        kwargs['data'] = json.loads(self.request.body)
        if 'pk' in self.kwargs:
            kwargs['instance'] = self.get_object()
        return kwargs

    def get_object(self):
        if 'pk' in self.kwargs:
            return self.model_class.objects.get(pk=self.kwargs['pk'])
        raise ValueError("Attempted to get an object by 'pk', but no 'pk' is present. Missing urlconf parameter?")

    def ng_query(self, request, *args, **kwargs):
        """
        Used when angular's query() method is called
        Build an array of all objects, return json response
        """
        objects = []
        for obj in self.model_class.objects.all():
            objects.append(self.build_model_dict(obj))
        return self.build_json_response(objects)

    def ng_get(self, request, *args, **kwargs):
        """
        Used when angular's get() method is called
        Returns a JSON response of a single object dictionary
        """
        return self.build_json_response(self.build_model_dict(self.get_object()))

    def ng_save(self, request, *args, **kwargs):
        """
        Called on $save()
        Use modelform to save new object or modify an existing one
        """
        form = self.get_form(self.get_form_class())
        if form.is_valid():
            obj = form.save()
            return self.build_json_response(self.build_model_dict(obj))
        raise ValidationError("Form not valid", form.errors)

    def ng_delete(self, request, *args, **kwargs):
        """
        Delete object and return it's data in JSON encoding
        """
        obj = self.get_object()
        obj.delete()
        return self.build_json_response(self.build_model_dict(obj))
