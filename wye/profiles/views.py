from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.views.generic.list import ListView
from django.views.generic import UpdateView, DetailView

from wye.base.constants import WorkshopStatus
from wye.organisations.models import Organisation
from wye.workshops.models import Workshop

from . import models
from .forms import UserProfileForm


class ProfileView(DetailView):
    model = models.Profile
    template_name = 'profile/index.html'
    slug_field = 'user__username'

    def get_context_data(self, *args, **kwargs):
        slug = self.kwargs['slug']
        self.object = self.model.objects.get(user__username=slug)
        context = super(
            ProfileView, self).get_context_data(*args, **kwargs)
        return context


class UserDashboard(ListView):
    model = models.Profile
    template_name = 'profile/dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        user_profile = models.Profile.objects.get(
            user__id=self.request.user.id)
        if not user_profile.get_user_type:
            return redirect('profiles:profile_create')
        return super(UserDashboard, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserDashboard, self).get_context_data(**kwargs)
        user_profile = models.Profile.objects.get(
            user__id=self.request.user.id)

        for each_type in user_profile.get_user_type:
            if each_type == 'Tutor':
                context['is_tutor'] = True
                context['workshop_requested_tutor'] = Workshop.objects.filter(
                    presenter=self.request.user, status=WorkshopStatus.REQUESTED)
                context['workshop_completed_tutor'] = Workshop.objects.filter(
                    presenter=self.request.user, status=WorkshopStatus.COMPLETED)
            if each_type == 'Regional-Lead':
                context['is_regional_lead'] = True
                context['workshops_accepted_under_rl'] = Workshop.objects.filter(
                    status=WorkshopStatus.ACCEPTED)
                context['workshops_pending_under_rl'] = Workshop.objects.filter(
                    status=WorkshopStatus.REQUESTED)
                context['interested_tutors'] = models.Profile.objects.filter(
                    usertype__slug='Tutor',
                    interested_locations__name__in=user_profile.get_interested_locations).exclude(
                    user__id=self.request.user.id).count()
                context['interested_locations'] = Organisation.objects.filter(
                    location__name__in=user_profile.get_interested_locations).count()
            if each_type == 'College-POC':
                context['is_college_poc'] = True
                context['organisation_users'] = models.Profile.objects.filter(
                    user__id__in=Organisation.objects.filter(
                        created_by__id=self.request.user.id).values_list(
                        'user', flat=True)).exclude(user=self.request.user)
                context['workshop_requested_under_poc'] = Workshop.objects.filter(
                    status=WorkshopStatus.REQUESTED,
                    requester=Organisation.objects.filter(
                        created_by__id=self.request.user.id))
                context['workshops_accepted_under_poc'] = Workshop.objects.filter(
                    status=WorkshopStatus.ACCEPTED,
                    requester=Organisation.objects.filter(
                        created_by__id=self.request.user.id))
            if each_type == 'Admin':
                context['is_admin'] = True
                context['workshops_by_status'] = Workshop.objects.all().order_by(
                    'status')
                context['workshops_by_region'] = Workshop.objects.all().order_by(
                    'location')
        return context


class ProfileEditView(UpdateView):
    model = models.Profile
    template_name = 'profile/update.html'
    form_class = UserProfileForm
    slug_field = 'user__username'

    def form_valid(self, form):
        return super(ProfileEditView, self).form_valid(form)

    def get_success_url(self):
        return reverse('profiles:profile-page', kwargs={'slug': self.object.slug})

    def dispatch(self, *args, **kwargs):
        if self.request.user.pk == self.get_object().pk:
            return super(ProfileEditView, self).dispatch(*args, **kwargs)
        else:
            raise PermissionDenied
