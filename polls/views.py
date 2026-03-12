import logging

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import F
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from .models import Choice, Question

logger = logging.getLogger(__name__)


class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[
            :5
        ]


class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"
    def get_queryset(self):
         """
         Excludes any questions that aren't published yet.
         """
         return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"


def vote(request, question_id):
    # same as above, no changes needed.
    ...


def vote(request, question_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    except (KeyError, Choice.DoesNotExist):
        logger.warning(
            "Vote request missing or invalid choice; question=%s remote_addr=%s",
            question_id,
            request.META.get("REMOTE_ADDR"),
        )
        # Redisplay the question voting form.
        return render(
            request,
            "polls/detail.html",
            {
                "question": question,
                "error_message": "You didn't select a choice.",
            },
        )
    else:
        selected_choice.votes = F("votes") + 1
        selected_choice.save()
        logger.info(
            "Vote recorded: question=%s choice=%s user=%s remote_addr=%s",
            question_id,
            selected_choice.id,
            request.user if request.user.is_authenticated else "anon",
            request.META.get("REMOTE_ADDR"),
        )
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            logger.info(
                "Login success: user=%s remote_addr=%s",
                user.username,
                request.META.get("REMOTE_ADDR"),
            )
            return redirect("polls:index")

        logger.warning(
            "Login failed: username=%s remote_addr=%s",
            username,
            request.META.get("REMOTE_ADDR"),
        )
        return render(
            request,
            "polls/login.html",
            {"error_message": "Invalid username or password."},
        )

    return render(request, "polls/login.html")


def logout_view(request):
    if request.user.is_authenticated:
        logger.info(
            "Logout: user=%s remote_addr=%s",
            request.user.username,
            request.META.get("REMOTE_ADDR"),
        )
        logout(request)

    return redirect("polls:index")


@csrf_exempt
def test(request):
    if request.method == "POST":
        body = request.body.decode("utf-8", errors="replace")
        logger.info(
            "POST /polls/test/ received from %s: %s",
            request.META.get("REMOTE_ADDR"),
            body,
        )
        return HttpResponse("Logged POST")

    else:
        return HttpResponse("No POST")