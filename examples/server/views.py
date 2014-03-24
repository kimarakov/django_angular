# -*- coding: utf-8 -*-
from django.shortcuts import redirect
from django.views.generic.base import TemplateView
from django.conf import settings
from server.forms import SubscriptionFormWithNgValidation, SubscriptionFormWithNgModel, SubscriptionFormWithNgValidationAndModel


class SubscribeFormView(TemplateView):
    def get_context_data(self, form=None, **kwargs):
        context = super(SubscribeFormView, self).get_context_data(**kwargs)
        form.fields['height'].widget.attrs['step'] = 0.05  # Ugly hack to set step size
        context.update(form=form, with_ws4redis=hasattr(settings, 'WEBSOCKET_URL'))
        return context

    def get(self, request, **kwargs):
        form = self.form()
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)

    def post(self, request, **kwargs):
        form = self.form(request.POST)
        if form.is_valid():
            return redirect('form_data_valid')
        context = self.get_context_data(form=form, **kwargs)
        return self.render_to_response(context)


class SubscribeViewWithFormValidation(SubscribeFormView):
    template_name = 'subscribe-form.html'
    form = SubscriptionFormWithNgValidation


class SubscribeViewWithModelForm(SubscribeFormView):
    template_name = 'subscribe-form-with-model.html'
    form = SubscriptionFormWithNgModel


class SubscribeViewWithModelFormAndValidation(SubscribeFormView):
    template_name = 'subscribe-form-with-model.html'
    form = SubscriptionFormWithNgValidationAndModel


class Ng3WayDataBindingView(SubscribeViewWithModelForm):
    template_name = 'three-way-data-binding.html'


class NgFormDataValidView(TemplateView):
    """
    This view just displays a success message, when a valid form was posted successfully.
    """
    template_name = 'form-data-valid.html'

    def get_context_data(self, **kwargs):
        context = super(NgFormDataValidView, self).get_context_data(**kwargs)
        context.update(with_ws4redis=hasattr(settings, 'WEBSOCKET_URL'))
        return context
