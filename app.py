from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

MODEL_NAME = "gpt-4o-mini-2024-07-18"

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(debug=True)
