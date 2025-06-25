from flask import Flask, render_template, request, jsonify, url_for
import uuid
from dotenv import load_dotenv
import os
from openai import OpenAI
import PyPDF2

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)
MODEL_NAME = "gpt-4o-mini-2024-07-18"

app = Flask(__name__)
UPLOAD_FOLDER = "static"

@app.route("/")
def index():
    return render_template("index.html", project_name="The AI Company")

@app.route("/resume-generator")
def resume_generator():
    return render_template("resume_generator.html")

@app.route("/resume-generator-json", methods=["POST"])
def resume_generator_json():
    data = request.get_json()
    name = data.get("name", "")
    email = data.get("email", "")
    skills = data.get("skills", "")
    educations = data.get("educations", [])
    experiences = data.get("experiences", [])

    prompt = f"Generate a professional resume:\nName: {name}\nEmail: {email}\n\n"
    if skills:
        prompt += f"Skills: {skills}\n\n"
    if experiences:
        prompt += "Job Experience:\n"
        for exp in experiences:
            if exp["title"] and exp["desc"]:
                prompt += f"{exp['title']} ({exp['start']} to {exp['end']}): {exp['desc']}\n"
    if educations:
        prompt += "\nEducation:\n"
        for edu in educations:
            if edu["school"] and edu["degree"]:
                prompt += f"{edu['degree']} from {edu['school']} (Graduated: {edu['grad']})\n"
    prompt += "\nInclude a professional summary at the top."

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional resume writer."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000,
            temperature=0.7
        )
        resume = response.choices[0].message.content
    except Exception as e:
        resume = f"Error generating resume: {e}"

    return jsonify({"resume": resume})

@app.route("/career-simulator", methods=["GET", "POST"])
def career_simulator():
    resume_url = None
    raw_resume = ""
    strengths = []
    improvements = []

    if request.method == "POST":
        file = request.files.get("resume_pdf")
        if file:
            filename = f"{uuid.uuid4().hex}.pdf"
            filepath = os.path.join("static", filename)
            file.save(filepath)
            resume_url = url_for("static", filename=filename)

            # ✅ Extract text from PDF using PyPDF2
            try:
                with open(filepath, "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    raw_resume = "\n".join([page.extract_text() or "" for page in reader.pages])
            except Exception as e:
                raw_resume = f"(Error reading PDF: {e})"

            # Summarize into 3 strengths & 3 improvements
            prompt = (
                f"Here is a resume:\n\n{raw_resume}\n\n"
                "As a recruiter, give a concise review:\n"
                "List:\n"
                "1. Three strengths of this resume.\n"
                "2. Three areas where it could be improved.\n"
                "Reply in this exact format:\n"
                "Strengths:\n- ...\n- ...\n- ...\nImprovements:\n- ...\n- ...\n- ..."
            )

            try:
                response = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a recruiter reviewing resumes."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                text = response.choices[0].message.content

                if "Strengths:" in text and "Improvements:" in text:
                    strengths_text = text.split("Strengths:")[1].split("Improvements:")[0].strip()
                    improvements_text = text.split("Improvements:")[1].strip()
                    strengths = [line.strip("- ").strip() for line in strengths_text.splitlines() if line.strip()]
                    improvements = [line.strip("- ").strip() for line in improvements_text.splitlines() if line.strip()]
            except Exception as e:
                improvements = [f"Error: {e}"]

    return render_template(
        "career_simulator.html",
        resume_url=resume_url,
        raw_resume=raw_resume,
        initial_strengths=strengths,
        initial_improvements=improvements
    )

@app.route("/api/ask-career", methods=["POST"])
def ask_career():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    resume_text = data.get("resume_text", "").strip()

    if not prompt or not resume_text:
        return jsonify({"response": "Missing question or resume text."}), 400

    full_prompt = (
        f"Here is the resume:\n\n{resume_text}\n\n"
        f"The user asks: {prompt}\n\n"
        "As a recruiter, respond with helpful, specific feedback that uses the resume context."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a recruiter reviewing resumes. Respond with practical, specific advice."
                },
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.7,
            max_tokens=600,
        )
        reply = response.choices[0].message.content
        return jsonify({"response": reply})
    except Exception as e:
        return jsonify({"response": f"Error generating answer: {str(e)}"}), 500


@app.route("/about-us")
def about_us():
    return render_template("about_us.html", project_name="The AI Company")

@app.route("/interview-coach")
def interview_coach():
    return render_template("interview_coach.html", project_name="The AI Company")

@app.route("/api/interview-chat", methods=["POST"])
def interview_chat():
    user_message = request.get_json().get("message", "")
    if not user_message:
        return jsonify({"reply": "Please type a question or response."})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a professional interview coach conducting a mock job interview. Ask realistic questions and give brief feedback on responses."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
    except Exception as e:
        reply = f"Error generating response: {e}"

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(debug=True)
