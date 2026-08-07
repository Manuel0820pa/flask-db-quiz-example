from .models import Question, Quiz, QuizScore

from flask import Blueprint, render_template, request

from . import db

bp = Blueprint("quizzes", __name__)

# Set up the routes
@bp.route("/")
def index():
    quizzes = db.session.execute(db.select(Quiz)).scalars().all()
    return render_template("index.html", quizzes=quizzes)


@bp.route("/quizzes/<quiz_id>")
def quiz(quiz_id):
    quiz = db.get_or_404(Quiz, quiz_id)
    questions = Quiz.questions_for_quiz(quiz_id)
    return render_template("quiz.html", quiz=quiz, questions=questions)


@bp.route("/quizzes/<quiz_id>/scores", methods=["GET", "POST"])
def app_add(quiz_id):
    if request.method == "POST":
        questions = Quiz.questions_for_quiz(quiz_id)
        # iterate over questions and check answers
        num_correct = 0
        for question in questions:
            if request.form.get(question.form_name) == question.answer:
                num_correct += 1
        percent_correct = (num_correct / len(questions)) * 100
        quiz_score = QuizScore(player=request.form["player"] or "Anonymous", score=percent_correct, quiz_id=quiz_id)
        db.session.add(quiz_score)
        db.session.commit()
        return (
            render_template("_score.html", quiz_score=quiz_score),
            200,
            {"HX-Trigger": "updateScores"},
        )
    else:
        # Always fetch scores and display them
        result = db.session.execute(
            db.select(QuizScore.player, QuizScore.score, db.func.max(QuizScore.score).label("max_score"))
            .where(QuizScore.quiz_id == quiz_id)
            .group_by(QuizScore.player, QuizScore.score)
            .order_by(db.desc("max_score"))
        ).all()
        return render_template("_scores.html", player_scores=result)
