from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import (
    CreateView,
    DetailView,
    FormView,
    ListView,
    TemplateView,
    CreateView,
    DetailView,
    FormView,
    ListView,
    UpdateView,
    View,
)

from django.http import JsonResponse, Http404
from django.utils import timezone
import json

from .services import parse_word_file
from accounts.decorators import lecturer_required
from .forms import (
    EssayForm,
    MCQuestionForm,
    MCQuestionFormSet,
    QuestionForm,
    QuizAddForm,
    QuizImportForm
)
from .models import (
    Course,
    EssayQuestion,
    MCQuestion,
    Progress,
    Question,
    Quiz,
    Sitting,
    QuizAttempt,
    UserResponse,
    Choice
)


# ########################################################
# Quiz Views
# ########################################################


@method_decorator([login_required, lecturer_required], name='dispatch')
class QuizCreateView(CreateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = 'quiz/quiz_form.html'
    
    def get_initial(self):
        initial = super().get_initial()
        course = get_object_or_404(Course, slug=self.kwargs['slug'])
        initial['course'] = course
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, slug=self.kwargs['slug'])
        return context

    def form_valid(self, form):
        form.instance.course = get_object_or_404(Course, slug=self.kwargs['slug'])
        self.object = form.save()
        messages.success(self.request, "Quiz created successfully.")
        return redirect('mc_create', slug=self.kwargs['slug'], quiz_id=self.object.id)

@method_decorator([login_required, lecturer_required], name='dispatch')
class QuizImportView(View):
    def get(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        form = QuizImportForm()
        return render(request, 'quiz/quiz_import.html', {'form': form, 'course': course})
        
    def post(self, request, slug):
        course = get_object_or_404(Course, slug=slug)
        form = QuizImportForm(request.POST, request.FILES)
        
        if form.is_valid():
            title = form.cleaned_data['title']
            description = form.cleaned_data['description']
            file = request.FILES['file']
            
            try:
                # Parse file
                parsed_questions = parse_word_file(file)
                
                if not parsed_questions:
                    messages.error(request, "No questions found in file.")
                    return render(request, 'quiz/quiz_import.html', {'form': form, 'course': course})
                    
                # Create Quiz
                quiz = Quiz.objects.create(
                    title=title,
                    description=description,
                    course=course,
                    category='exam', # default
                    time_limit=form.cleaned_data['time_limit'],
                    max_attempts=form.cleaned_data['max_attempts'],
                    start_date=form.cleaned_data['start_date'],
                    end_date=form.cleaned_data['end_date']
                )
                
                # Create Questions
                count = 0
                for q_data in parsed_questions:
                    question = MCQuestion.objects.create(
                        content=q_data['content']
                    )
                    question.quiz.add(quiz)
                    
                    has_correct = False
                    for c_data in q_data['choices']:
                        Choice.objects.create(
                            question=question,
                            choice_text=c_data['text'],
                            correct=c_data['correct']
                        )
                        if c_data['correct']:
                            has_correct = True
                    
                    if not has_correct and q_data['choices']:
                        # Auto mark first as correct if none marked? No, better warn.
                        # For now, just logging or relying on parser quality.
                        pass
                        
                    count += 1
                    
                messages.success(request, f"Quiz '{title}' imported with {count} questions.")
                return redirect('quiz_index', slug=course.slug)
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                return render(request, 'quiz/quiz_import.html', {'form': form, 'course': course})
                
        return render(request, 'quiz/quiz_import.html', {'form': form, 'course': course})


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizUpdateView(UpdateView):
    model = Quiz
    form_class = QuizAddForm
    template_name = "quiz/quiz_form.html"

    def get_object(self, queryset=None):
        return get_object_or_404(Quiz, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        return context

    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            return redirect("quiz_index", self.kwargs["slug"])


@login_required
@lecturer_required
def quiz_delete(request, slug, pk):
    quiz = get_object_or_404(Quiz, pk=pk)
    quiz.delete()
    messages.success(request, "Quiz successfully deleted.")
    return redirect("quiz_index", slug=slug)


@login_required
def quiz_list(request, slug):
    course = get_object_or_404(Course, slug=slug)
    quizzes = Quiz.objects.filter(course=course).order_by("-timestamp")
    return render(
        request, "quiz/quiz_list.html", {"quizzes": quizzes, "course": course}
    )


# ########################################################
# Multiple Choice Question Views
# ########################################################


@method_decorator([login_required, lecturer_required], name="dispatch")
class MCQuestionCreate(CreateView):
    model = MCQuestion
    form_class = MCQuestionForm
    template_name = "quiz/mcquestion_form.html"

    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs["quiz"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
    #     return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = get_object_or_404(Course, slug=self.kwargs["slug"])
        context["quiz_obj"] = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])
        context["quiz_questions_count"] = Question.objects.filter(
            quiz=self.kwargs["quiz_id"]
        ).count()
        if self.request.method == "POST":
            context["formset"] = MCQuestionFormSet(self.request.POST)
        else:
            context["formset"] = MCQuestionFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context["formset"]
        if formset.is_valid():
            with transaction.atomic():
                # Save the MCQuestion instance without committing to the database yet
                self.object = form.save(commit=False)
                self.object.save()

                # Retrieve the Quiz instance
                quiz = get_object_or_404(Quiz, id=self.kwargs["quiz_id"])

                # set the many-to-many relationship
                self.object.quiz.add(quiz)

                # Save the formset (choices for the question)
                formset.instance = self.object
                formset.save()

                if "another" in self.request.POST:
                    return redirect(
                        "mc_create",
                        slug=self.kwargs["slug"],
                        quiz_id=self.kwargs["quiz_id"],
                    )
                return redirect("quiz_index", slug=self.kwargs["slug"])
        else:
            return self.form_invalid(form)


# ########################################################
# Quiz Progress and Marking Views
# ########################################################


@method_decorator([login_required], name="dispatch")
class QuizUserProgressView(TemplateView):
    template_name = "quiz/progress.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress, _ = Progress.objects.get_or_create(user=self.request.user)
        context["cat_scores"] = progress.list_all_cat_scores
        context["exams"] = progress.show_exams()
        context["exams_counter"] = context["exams"].count()
        return context


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingList(ListView):
    model = Sitting
    template_name = "quiz/quiz_marking_list.html"

    def get_queryset(self):
        queryset = Sitting.objects.filter(complete=True)
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                quiz__course__allocated_course__lecturer__pk=self.request.user.id
            )
        quiz_filter = self.request.GET.get("quiz_filter")
        if quiz_filter:
            queryset = queryset.filter(quiz__title__icontains=quiz_filter)
        user_filter = self.request.GET.get("user_filter")
        if user_filter:
            queryset = queryset.filter(user__username__icontains=user_filter)
        return queryset


@method_decorator([login_required, lecturer_required], name="dispatch")
class QuizMarkingDetail(DetailView):
    model = Sitting
    template_name = "quiz/quiz_marking_detail.html"

    def post(self, request, *args, **kwargs):
        sitting = self.get_object()
        question_id = request.POST.get("qid")
        if question_id:
            question = Question.objects.get_subclass(id=int(question_id))
            if int(question_id) in sitting.get_incorrect_questions:
                sitting.remove_incorrect_question(question)
            else:
                sitting.add_incorrect_question(question)
        return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["questions"] = self.object.get_questions(with_answers=True)
        return context


# ########################################################
# Quiz Taking View
# ########################################################


# ########################################################
# Quiz Taking Views (Redesigned)
# ########################################################

@method_decorator([login_required], name="dispatch")
class QuizStartView(View):
    def get(self, request, slug, pk):
        course = get_object_or_404(Course, pk=pk)
        quiz = get_object_or_404(Quiz, slug=slug)
        
        # Check if quiz is drafted
        if quiz.draft and not request.user.is_lecturer:
             messages.warning(request, "This quiz is not available.")
             return redirect("quiz_index", slug=course.slug)

        # Check attempts
        attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
        if quiz.max_attempts > 0 and attempts.count() >= quiz.max_attempts:
            messages.warning(request, f"You have reached the maximum number of attempts ({quiz.max_attempts}).")
            return redirect("quiz_index", slug=course.slug)

        # Create new attempt
        attempt = QuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            status="in_progress"
        )
        return redirect("quiz_take", pk=course.pk, slug=quiz.slug)


@method_decorator([login_required], name="dispatch")
@method_decorator([login_required], name="dispatch")
class QuizTake(TemplateView):
    template_name = "quiz/take_quiz.html"

    def dispatch(self, request, *args, **kwargs):
        self.course = get_object_or_404(Course, pk=self.kwargs["pk"])
        self.quiz = get_object_or_404(Quiz, slug=self.kwargs["slug"])
        
        # Get active attempt
        self.attempt = QuizAttempt.objects.filter(
            user=request.user, 
            quiz=self.quiz, 
            status="in_progress"
        ).first()

        if not self.attempt:
            # If no active attempt, redirect to start (or index)
            # This prevents accessing /take/ url directly without starting
            return redirect("quiz_start", pk=self.course.pk, slug=self.quiz.slug)

        return super().dispatch(request, *args, **kwargs)



    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["course"] = self.course
        context["quiz"] = self.quiz
        context["attempt"] = self.attempt
        
        # Get all questions
        questions = self.quiz.question_set.all().select_subclasses()
        context["questions"] = questions
        
        # Get existing user responses (to show selected answers)
        # Use a dictionary k=QuestionID, v=SelectedChoiceID/Text
        responses = UserResponse.objects.filter(attempt=self.attempt)
        context["user_answers"] = {
            r.question_id: r.selected_choice_id for r in responses if r.selected_choice
        }
        # Add essay answers
        essay_answers = {
            r.question_id: r.text_answer for r in responses if r.text_answer
        }
        context["user_text_answers"] = essay_answers
        
        # Calculate time remaining
        if self.quiz.time_limit > 0:
            elapsed = (timezone.now() - self.attempt.start_time).total_seconds()
            remaining = (self.quiz.time_limit * 60) - elapsed
            context["time_remaining"] = max(0, remaining)
        
        return context


@method_decorator([login_required], name="dispatch")
class QuizSaveAnswer(View):
    def post(self, request):
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
             return JsonResponse({"success": False, "error": "Invalid request"}, status=400)
             
        data = json.loads(request.body)
        attempt_id = data.get("attempt_id")
        question_id = data.get("question_id")
        answer_data = data.get("answer") # choice_id or text
        
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
        if attempt.status != "in_progress":
            return JsonResponse({"success": False, "error": "Quiz is not in progress"})
            
        question = get_object_or_404(Question, id=question_id)
        
        # Get or create response
        response, created = UserResponse.objects.get_or_create(
            attempt=attempt,
            question=question
        )
        
        # Save answer based on type
        # Basic check if it's Choice ID (int) or Text
        # Assuming MCQuestion logic for now
        is_mcq = MCQuestion.objects.filter(id=question_id).exists()
        
        if is_mcq:
            try:
                choice = Choice.objects.get(id=int(answer_data))
                response.selected_choice = choice
                response.text_answer = None
            except:
                pass # invalid choice
        else:
            response.text_answer = answer_data
            response.selected_choice = None
            
        response.save()
        
        return JsonResponse({"success": True})


@method_decorator([login_required], name="dispatch")
class QuizSubmit(View):
    def post(self, request, pk, slug):
        course = get_object_or_404(Course, pk=pk)
        quiz = get_object_or_404(Quiz, slug=slug)
        attempt = QuizAttempt.objects.filter(
            user=request.user, 
            quiz=quiz, 
            status="in_progress"
        ).first()
        
        if attempt:
            # Mark as submitted
            attempt.status = "submitted"
            attempt.submit_time = timezone.now()
            attempt.save()
            
            # Trigger Auto Grading (Simple Version)
            self.grade_attempt(attempt)
            
        return redirect("quiz_result", pk=course.pk, slug=quiz.slug, attempt_id=attempt.id)

    def grade_attempt(self, attempt):
        responses = UserResponse.objects.filter(attempt=attempt)
        score = 0
        for r in responses:
            if r.selected_choice and r.selected_choice.correct:
                r.is_correct = True
                r.marks = 1 # Assuming 1 mark per question for now
                score += 1
            else:
                r.is_correct = False
                r.marks = 0
            r.save()
        
        attempt.score = score
        attempt.status = "graded" # Auto graded
        attempt.save()


@method_decorator([login_required], name="dispatch")
class QuizResultDetail(DetailView):
    model = QuizAttempt
    template_name = "quiz/result.html"
    context_object_name = "attempt" # standardizing

    def get_object(self):
        return get_object_or_404(
            QuizAttempt, 
            id=self.kwargs["attempt_id"], 
            user=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["quiz"] = self.object.quiz
        context["course"] = get_object_or_404(Course, pk=self.kwargs["pk"])
        
        # Breakdown
        context["questions"] = self.object.responses.select_related('question').all()
        return context
